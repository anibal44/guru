# Guru — Setup & API Keys

Everything needed for a full, zero-failure execution of the 9-step wizard.

---

## API Keys (Environment Variables)

| Variable | Required | Used In | Purpose |
|----------|----------|---------|---------|
| `GEMINI_API_KEY` | **YES** | Steps 5, 6, 8a | Gemini 2.0 Flash (transcript analysis, course outline) + Gemini image gen (hero image) |
| `V0_API_KEY` | Optional | Step 8b | v0 API for AI-generated landing pages. Without it, falls back to HTML template (still works). |
| `DEEPGRAM_API_KEY` | **Recommended** | Step 4 | Deepgram Nova-2 — PRIMARY transcription source when `--deepgram-first` flag is used. Higher quality than YouTube auto-captions. Free $200 credits at signup. |
| `CLOUDFLARE_API_TOKEN` | No (OAuth) | Step 9 | Wrangler uses OAuth login (`wrangler login`). No env var needed if already logged in. |

### Quick Export Block

Copy-paste this into your shell before running the wizard:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
export V0_API_KEY="v1:your-project-id:vcp_your-token-here"
export DEEPGRAM_API_KEY="your-deepgram-api-key-here"
```

### Where to Get Each Key

| Key | URL | Notes |
|-----|-----|-------|
| GEMINI_API_KEY | https://aistudio.google.com/apikey | Free tier: 1500 req/day on Flash. Needed for analysis + image gen. |
| V0_API_KEY | https://v0.dev/chat/settings (API tab) | Requires v0 Pro/Team plan ($20/mo). Model: `v0-1.5-md`. |
| DEEPGRAM_API_KEY | https://console.deepgram.com | Free $200 credits on signup. Only needed if many videos lack captions. |
| Wrangler (Cloudflare) | `wrangler login` | OAuth — opens browser. Already logged in as `anibalpsviegas@gmail.com`. |

---

## CLI Tools Required

| Tool | Check | Install |
|------|-------|---------|
| `python3` | `python3 --version` | Pre-installed on macOS |
| `wrangler` | `which wrangler` | `npm i -g wrangler` |
| `yt-dlp` | `which yt-dlp` | `brew install yt-dlp` |

---

## Python Packages Required

| Package | Check | Install |
|---------|-------|---------|
| `google-genai` | `python3 -c "from google import genai; print('OK')"` | `pip3 install google-genai` |
| `youtube-transcript-api` | `python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; print('OK')"` | `pip3 install youtube-transcript-api` |
| `scrapetube` | `python3 -c "import scrapetube; print('OK')"` | `pip3 install scrapetube` |
| `deepgram-sdk` (optional) | `python3 -c "from deepgram import DeepgramClient; print('OK')"` | `pip3 install deepgram-sdk` |

---

## Pre-Flight Verification Script

Run this before a demo to verify everything is ready:

```bash
echo "=== Guru Pre-Flight Check ==="

# API Keys
echo -n "GEMINI_API_KEY: "; [ -n "$GEMINI_API_KEY" ] && echo "${GEMINI_API_KEY:0:10}..." || echo "MISSING"
echo -n "V0_API_KEY:     "; [ -n "$V0_API_KEY" ] && echo "${V0_API_KEY:0:10}..." || echo "NOT SET (fallback OK)"
echo -n "DEEPGRAM:       "; [ -n "$DEEPGRAM_API_KEY" ] && echo "${DEEPGRAM_API_KEY:0:10}..." || echo "NOT SET (optional)"

# CLI Tools
echo -n "python3:        "; python3 --version 2>&1 | head -1
echo -n "wrangler:       "; wrangler --version 2>&1 | head -1
echo -n "yt-dlp:         "; yt-dlp --version 2>&1 | head -1
echo -n "wrangler auth:  "; wrangler whoami 2>&1 | grep -o "logged in.*" | head -1

# Python Packages
echo -n "google-genai:   "; python3 -c "from google import genai; print('OK')" 2>&1
echo -n "yt-transcript:  "; python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; print('OK')" 2>&1
echo -n "scrapetube:     "; python3 -c "import scrapetube; print('OK')" 2>&1

# Scripts
echo -n "transcript dl:  "; [ -f ~/bin/download_transcripts_v2.py ] && echo "OK" || echo "MISSING"
echo -n "analyze:        "; [ -f ~/.claude/skills/guru/scripts/analyze_transcripts.py ] && echo "OK" || echo "MISSING"
echo -n "outline:        "; [ -f ~/.claude/skills/guru/scripts/generate_course_outline.py ] && echo "OK" || echo "MISSING"
echo -n "hero image:     "; [ -f ~/.claude/skills/guru/scripts/generate_hero_image.py ] && echo "OK" || echo "MISSING"
echo -n "landing page:   "; [ -f ~/.claude/skills/guru/scripts/generate_landing_page.py ] && echo "OK" || echo "MISSING"
echo -n "deploy:         "; [ -f ~/.claude/skills/guru/scripts/deploy_pages.sh ] && echo "OK" || echo "MISSING"
echo -n "template:       "; [ -f ~/.claude/skills/guru/templates/landing-page/index.html ] && echo "OK" || echo "MISSING"

echo "=== Done ==="
```

---

## What Breaks Without Each Key

| Missing Key | Impact | Workaround |
|-------------|--------|------------|
| `GEMINI_API_KEY` | **Steps 5, 6, 8a all fail** — no analysis, no outline, no hero image | None. This is the only hard requirement. |
| `V0_API_KEY` | Step 8b uses template fallback instead of AI-generated page | Template still produces a good page. No action needed. |
| `DEEPGRAM_API_KEY` | `--deepgram-first` won't work; falls back to YouTube auto-captions only (lower quality) | YouTube captions still work. Transcripts will be lower quality but usable. |
| Wrangler not logged in | Step 9 deploy fails | Show page locally via `file://` URL. Deploy after demo. |
