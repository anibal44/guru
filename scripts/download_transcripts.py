#!/usr/bin/env python3
"""
Guru — Transcript Downloader
Self-contained transcript downloader for the Guru course creator skill.

Fallback chain:
  1. youtube-transcript-api  (fast, no subprocess — but YouTube may IP-block)
  2. yt-dlp subtitle extraction  (reliable with cookies, no audio download)
  3. Deepgram Nova-2 audio transcription  (requires DEEPGRAM_API_KEY)

Cookie support (fixes IP blocking):
  Export cookies once:  yt-dlp --cookies-from-browser chrome --cookies ~/.cache/guru/yt-cookies.txt --skip-download "https://www.youtube.com"
  Then pass:  --cookies ~/.cache/guru/yt-cookies.txt

Usage:
    python3 download_transcripts.py --channel aliabdaal --limit 50 --output ./transcripts
    python3 download_transcripts.py --channel aliabdaal --limit 50 --output ./transcripts --cookies ~/.cache/guru/yt-cookies.txt
    python3 download_transcripts.py --channel aliabdaal --limit 50 --output ./transcripts --deepgram
"""

import subprocess
import json
import sys
import os
import re
import argparse
import tempfile
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ─── Optional imports ────────────────────────────────────────────────────────

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _YT_API_AVAILABLE = True
except ImportError:
    _YT_API_AVAILABLE = False
    print("WARNING: youtube-transcript-api not installed (pip3 install youtube-transcript-api)")

try:
    import scrapetube
    _SCRAPETUBE_AVAILABLE = True
except ImportError:
    _SCRAPETUBE_AVAILABLE = False

_DEEPGRAM_AVAILABLE = False
try:
    from deepgram import DeepgramClient
    _DEEPGRAM_AVAILABLE = True
except ImportError:
    pass

# ─── Constants ───────────────────────────────────────────────────────────────

COOKIE_CACHE = Path.home() / ".cache" / "guru" / "yt-cookies.txt"
DEFAULT_THREADS = 10
DEFAULT_OUTPUT = Path.home() / "Documents" / "youtube_transcripts"

# ─── Thread-safe state ───────────────────────────────────────────────────────

_lock = threading.Lock()
_stats = {"done": 0, "success": 0, "total": 0, "youtube": 0, "yt-dlp": 0, "deepgram": 0}
_yt_api_blocked = False  # Once True, skip youtube-transcript-api for all remaining videos
_deepgram_client = None


# ─── Helpers ─────────────────────────────────────────────────────────────────


def find_ytdlp():
    """Locate yt-dlp binary."""
    result = subprocess.run(["which", "yt-dlp"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    # Check common paths
    for p in [
        Path.home() / ".local" / "bin" / "yt-dlp",
        Path("/opt/homebrew/bin/yt-dlp"),
        Path("/usr/local/bin/yt-dlp"),
    ]:
        if p.exists():
            return str(p)
    return "yt-dlp"


YT_DLP = find_ytdlp()


def init_deepgram():
    """Initialize Deepgram client."""
    global _deepgram_client
    if _deepgram_client is not None:
        return _deepgram_client
    key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not key:
        return None
    if not _DEEPGRAM_AVAILABLE:
        print("   WARNING: deepgram-sdk not installed (pip3 install deepgram-sdk)")
        return None
    try:
        _deepgram_client = DeepgramClient()
        return _deepgram_client
    except Exception as e:
        print(f"   ERROR initializing Deepgram: {e}")
        return None


# ─── Video listing ───────────────────────────────────────────────────────────


def get_channel_videos(channel_name, limit=None, cookies_path=None):
    """Get video list from a YouTube channel. Tries scrapetube first, yt-dlp fallback."""
    print(f"Fetching videos from @{channel_name}...")

    # Try scrapetube (fast, no subprocess)
    if _SCRAPETUBE_AVAILABLE:
        try:
            videos_raw = list(scrapetube.get_channel(channel_username=channel_name))
            videos = []
            for v in videos_raw:
                videos.append({
                    "video_id": v.get("videoId"),
                    "title": v.get("title", {}).get("runs", [{}])[0].get("text", "Untitled"),
                    "published": v.get("publishedTimeText", {}).get("simpleText", ""),
                    "url": f"https://www.youtube.com/watch?v={v.get('videoId')}",
                })
                if limit and len(videos) >= limit:
                    break
            if videos:
                print(f"   Found {len(videos)} videos (scrapetube)")
                return videos
        except Exception as e:
            print(f"   scrapetube failed: {e}")

    # Fallback: yt-dlp --flat-playlist
    print(f"   Falling back to yt-dlp...")
    try:
        cmd = [
            YT_DLP, "--flat-playlist",
            f"https://www.youtube.com/@{channel_name}/videos",
            "--print", "%(id)s\t%(title)s",
            "--playlist-items", f"1:{limit or 50}",
            "--remote-components", "ejs:github",
            "--no-warnings",
        ]
        if cookies_path and Path(cookies_path).exists():
            cmd.extend(["--cookies", str(cookies_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            vid_id = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else "Untitled"
            if vid_id:
                videos.append({
                    "video_id": vid_id,
                    "title": title,
                    "published": "",
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                })
        print(f"   Found {len(videos)} videos (yt-dlp)")
        return videos
    except Exception as e:
        print(f"   yt-dlp video listing failed: {e}")
        return []


# ─── Transcript method 1: youtube-transcript-api ─────────────────────────────


def get_transcript_yt_api(video_id):
    """Fast transcript via youtube-transcript-api. Returns (text, True) or (None, blocked)."""
    global _yt_api_blocked
    if _yt_api_blocked or not _YT_API_AVAILABLE:
        return None

    # Create per-thread instance (API is not thread-safe)
    api = YouTubeTranscriptApi()

    try:
        for lang in ["en", "en-US", "pt", "pt-BR", "es"]:
            try:
                transcript = api.fetch(video_id, languages=[lang])
                return " ".join(entry.text for entry in transcript)
            except Exception as e:
                etype = type(e).__name__
                if "RequestBlocked" in etype or "IPBlocked" in etype:
                    _yt_api_blocked = True
                    print(f"\n   ⚠️  youtube-transcript-api IP-blocked. Switching to yt-dlp subtitles.\n")
                    return None
                continue

        # Try any language
        try:
            transcript = api.fetch(video_id)
            return " ".join(entry.text for entry in transcript)
        except Exception as e:
            etype = type(e).__name__
            if "RequestBlocked" in etype or "IPBlocked" in etype:
                _yt_api_blocked = True
                print(f"\n   ⚠️  youtube-transcript-api IP-blocked. Switching to yt-dlp subtitles.\n")
            return None

    except Exception:
        return None


# ─── Transcript method 2: yt-dlp subtitle extraction ─────────────────────────


def parse_json3_subs(file_path):
    """Parse yt-dlp json3 subtitle file into plain text."""
    try:
        with open(file_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    texts = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            text = seg.get("utf8", "").replace("\n", " ").strip()
            if text:
                texts.append(text)

    if not texts:
        return None

    # Deduplicate consecutive repeats (auto-subs often duplicate)
    deduped = [texts[0]]
    for t in texts[1:]:
        if t != deduped[-1]:
            deduped.append(t)

    result = " ".join(deduped).strip()
    # Clean up extra whitespace
    result = re.sub(r"\s+", " ", result)
    return result if len(result) > 50 else None


def get_transcript_ytdlp(video_id, cookies_path=None):
    """Extract subtitles via yt-dlp (no audio download). Returns text or None."""
    with tempfile.TemporaryDirectory(prefix="guru_subs_") as tmp:
        tmp_path = Path(tmp)
        cmd = [
            YT_DLP,
            "--write-auto-sub", "--write-sub",
            "--sub-lang", "en.*,en",
            "--sub-format", "json3",
            "--skip-download",
            "--remote-components", "ejs:github",
            "--no-warnings", "--no-progress",
            "-o", str(tmp_path / "%(id)s.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        if cookies_path and Path(cookies_path).exists():
            cmd.extend(["--cookies", str(cookies_path)])

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

        # Find the subtitle file (could be .en.json3, .en-orig.json3, etc.)
        sub_files = sorted(tmp_path.glob(f"{video_id}*.json3"))
        if not sub_files:
            return None

        return parse_json3_subs(sub_files[0])


# ─── Transcript method 3: Deepgram audio transcription ───────────────────────


def get_transcript_deepgram(video_id, temp_dir, cookies_path=None):
    """Transcribe via Deepgram (downloads audio first). Returns text or None."""
    if _deepgram_client is None:
        return None

    # Download audio
    output_file = temp_dir / f"{video_id}.mp4"
    cmd = [
        YT_DLP,
        "-f", "18",  # 360p mp4 with audio — small and fast
        "--remote-components", "ejs:github",
        "--no-warnings", "--no-progress",
        "-o", str(output_file),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    if cookies_path and Path(cookies_path).exists():
        cmd.extend(["--cookies", str(cookies_path)])

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception:
        return None

    if not output_file.exists():
        # Check for other extensions
        possible = list(temp_dir.glob(f"{video_id}.*"))
        if possible:
            output_file = possible[0]
        else:
            return None

    try:
        with open(output_file, "rb") as f:
            buffer_data = f.read()

        response = _deepgram_client.listen.v1.media.transcribe_file(
            request=buffer_data,
            model="nova-2",
            smart_format=True,
            language="en",
        )
        transcript = response.results.channels[0].alternatives[0].transcript

        try:
            output_file.unlink()
        except Exception:
            pass

        return transcript if len(transcript) > 20 else None

    except Exception:
        try:
            output_file.unlink()
        except Exception:
            pass
        return None


# ─── Core download logic ─────────────────────────────────────────────────────


def download_transcript(video_data, temp_dir, cookies_path=None, use_deepgram=False):
    """Download transcript with cascading fallbacks.

    Order: youtube-transcript-api → yt-dlp subs → Deepgram
    """
    video_id = video_data["video_id"]
    transcript = None
    source = "none"

    # 1. youtube-transcript-api (fast, no subprocess)
    transcript = get_transcript_yt_api(video_id)
    if transcript:
        source = "youtube"

    # 2. yt-dlp subtitle extraction (reliable with cookies)
    if transcript is None:
        transcript = get_transcript_ytdlp(video_id, cookies_path)
        if transcript:
            source = "yt-dlp"

    # 3. Deepgram audio transcription (last resort)
    if transcript is None and use_deepgram:
        transcript = get_transcript_deepgram(video_id, temp_dir, cookies_path)
        if transcript:
            source = "deepgram"

    # Update progress
    with _lock:
        _stats["done"] += 1
        if transcript:
            _stats["success"] += 1
            if source in _stats:
                _stats[source] += 1

        if _stats["done"] % 10 == 0 or _stats["done"] == _stats["total"]:
            pct = (_stats["done"] / _stats["total"]) * 100
            methods = f"yt-api:{_stats['youtube']} yt-dlp:{_stats['yt-dlp']} dg:{_stats['deepgram']}"
            print(
                f"   [{_stats['done']:04d}/{_stats['total']}] "
                f"{pct:.0f}% — {_stats['success']} transcripts ({methods})"
            )
            sys.stdout.flush()

    video_data["transcript"] = transcript if transcript else "[Transcript not available]"
    video_data["source"] = source
    return video_data


# ─── Output ──────────────────────────────────────────────────────────────────


def save_results(results, output_dir, output_name):
    """Save results to JSON and Markdown files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success = sum(1 for r in results if r["transcript"] != "[Transcript not available]")
    by_source = {}
    for r in results:
        s = r.get("source", "none")
        by_source[s] = by_source.get(s, 0) + 1

    json_file = output_dir / f"{output_name}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    md_file = output_dir / f"{output_name}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# YouTube Transcripts — {output_name}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Videos:** {len(results)} | **Transcripts:** {success}\n")
        source_parts = [f"{k}: {v}" for k, v in by_source.items() if k != "none"]
        if source_parts:
            f.write(f"**Sources:** {', '.join(source_parts)}\n")
        f.write("\n---\n\n")

        for item in results:
            badge = f" [{item.get('source', 'none')}]" if item.get("source", "none") != "none" else ""
            f.write(f"## {item['title']}{badge}\n\n")
            f.write(f"- **URL:** {item['url']}\n")
            f.write(f"- **Published:** {item.get('published', 'N/A')}\n\n")
            f.write(item["transcript"])
            f.write("\n\n---\n\n")

    return json_file, md_file, success, by_source


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Guru transcript downloader — youtube-transcript-api → yt-dlp subs → Deepgram"
    )
    parser.add_argument("--channel", "-c", required=True, help="YouTube channel name (without @)")
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT), help="Output directory")
    parser.add_argument("--threads", "-t", type=int, default=DEFAULT_THREADS, help="Parallel threads (default: 10)")
    parser.add_argument("--limit", "-l", type=int, help="Max videos to process")
    parser.add_argument("--name", "-n", help="Output filename (without extension)")
    parser.add_argument("--cookies", help="Path to Netscape cookie file (fixes YouTube IP blocking)")
    parser.add_argument("--deepgram", "-d", action="store_true", help="Enable Deepgram as final fallback (requires DEEPGRAM_API_KEY)")

    args = parser.parse_args()

    # Resolve cookie path
    cookies_path = args.cookies
    if not cookies_path and COOKIE_CACHE.exists():
        cookies_path = str(COOKIE_CACHE)
        print(f"Using cached cookies: {cookies_path}")

    print("=" * 70)
    print("GURU TRANSCRIPT DOWNLOADER")
    print("=" * 70)
    print(f"Channel:  @{args.channel}")
    print(f"Threads:  {args.threads}")
    print(f"Cookies:  {cookies_path or 'none (may get IP-blocked)'}")
    print(f"Deepgram: {'yes' if args.deepgram else 'no'}")
    print(f"Start:    {datetime.now().strftime('%H:%M:%S')}")
    sys.stdout.flush()

    # Initialize Deepgram if requested
    if args.deepgram:
        client = init_deepgram()
        if client:
            print("   Deepgram client ready")
        else:
            print("   Deepgram unavailable — will use youtube-api + yt-dlp only")
            args.deepgram = False

    # Get video list
    videos = get_channel_videos(args.channel, args.limit, cookies_path)
    if not videos:
        print("No videos found!")
        sys.exit(1)

    output_name = args.name or f"{args.channel}_transcripts"
    print(f"\nProcessing {len(videos)} videos...")
    sys.stdout.flush()

    _stats["total"] = len(videos)
    _stats["done"] = 0
    _stats["success"] = 0
    _stats["youtube"] = 0
    _stats["ytdlp"] = 0
    _stats["deepgram"] = 0

    temp_dir = Path(args.output) / ".temp_audio"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Cap threads when using Deepgram (audio downloads are heavier)
    effective_threads = min(args.threads, 5) if args.deepgram else args.threads

    results = []
    with ThreadPoolExecutor(max_workers=effective_threads) as executor:
        futures = {
            executor.submit(
                download_transcript, v, temp_dir, cookies_path, args.deepgram
            ): v
            for v in videos
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                vd = futures[future]
                vd["transcript"] = "[Transcript not available]"
                vd["source"] = "none"
                results.append(vd)

    # Cleanup temp
    try:
        for f in temp_dir.glob("*"):
            f.unlink()
        temp_dir.rmdir()
    except Exception:
        pass

    # Save
    json_file, md_file, success, by_source = save_results(results, args.output, output_name)

    print(f"\n{'=' * 70}")
    print(f"DONE — {datetime.now().strftime('%H:%M:%S')}")
    print(f"Transcripts: {success}/{len(results)} ({success / len(results) * 100:.0f}%)")
    for src, count in sorted(by_source.items()):
        if src != "none":
            print(f"  {src}: {count}")
    if by_source.get("none", 0) > 0:
        print(f"  failed: {by_source['none']}")
    print(f"\nFiles:")
    print(f"  {json_file}")
    print(f"  {md_file}")

    if _yt_api_blocked and not cookies_path:
        print(f"\n{'=' * 70}")
        print("TIP: YouTube blocked your IP. Export cookies to fix this:")
        print(f"  yt-dlp --cookies-from-browser chrome --cookies {COOKIE_CACHE} --skip-download 'https://www.youtube.com'")
        print(f"  Then re-run with: --cookies {COOKIE_CACHE}")

    print("=" * 70)


if __name__ == "__main__":
    main()
