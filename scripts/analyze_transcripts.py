#!/usr/bin/env python3
"""
Guru — Transcript Analyzer
Sends merged transcripts to Gemini 2.0 Flash for topic extraction + course structure.
"""

import json
import sys
import os
import argparse
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed. Run: pip3 install google-genai")
    sys.exit(1)


MAX_TRANSCRIPTS = 200
MAX_CHARS_PER_TRANSCRIPT = 3000
MODEL = "gemini-2.0-flash"

ANALYSIS_PROMPT = """You are a world-class online course architect. You have been given transcripts from the top YouTube channels in the "{niche}" niche.

Your job:
1. Identify the CORE TOPICS these creators consistently teach
2. Extract the PAIN POINTS their audiences face (from questions, comments referenced, problems addressed)
3. Identify proven FRAMEWORKS and METHODOLOGIES the creators use
4. Map the natural PROGRESSION PATH from beginner to advanced
5. Find GAPS — topics the audience needs but creators haven't covered well
6. Design a COMPLETE COURSE STRUCTURE with 4-6 modules, each with 3-5 lessons

For each module and lesson, attribute which creator(s) inspired it.

IMPORTANT RULES:
- Course must be practical, not theoretical
- Each lesson must have a clear, actionable learning outcome
- Module order must follow a logical progression (foundations → advanced)
- Include a compelling course title and subtitle that would sell

Here are the transcripts from {num_channels} channels ({num_transcripts} videos):

{transcripts}
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "course_title": {"type": "string"},
        "course_subtitle": {"type": "string"},
        "target_audience": {"type": "string"},
        "core_topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "frequency": {"type": "string"},
                    "source_creators": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["topic", "frequency", "source_creators"]
            }
        },
        "pain_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "frameworks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "creator": {"type": "string"}
                },
                "required": ["name", "description", "creator"]
            }
        },
        "gaps": {
            "type": "array",
            "items": {"type": "string"}
        },
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "module_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "lessons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lesson_number": {"type": "integer"},
                                "title": {"type": "string"},
                                "learning_outcome": {"type": "string"},
                                "source_creators": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["lesson_number", "title", "learning_outcome", "source_creators"]
                        }
                    }
                },
                "required": ["module_number", "title", "description", "lessons"]
            }
        }
    },
    "required": ["course_title", "course_subtitle", "target_audience", "core_topics", "pain_points", "frameworks", "gaps", "modules"]
}


UNAVAILABLE_MARKERS = [
    "[Transcript not available]",
    "[Transcript não disponível]",
]


def load_transcripts(transcript_dir: Path) -> list[dict]:
    """Load all transcript JSON files from a directory.
    Compatible with both v1 (_transcripts) and v2 (_transcripts_v2) formats.
    """
    transcripts = []
    json_files = sorted(transcript_dir.glob("*.json"))

    for jf in json_files[:MAX_TRANSCRIPTS]:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            # Derive channel name from filename (handles both _transcripts and _transcripts_v2)
            channel = jf.stem.replace("_transcripts_v2", "").replace("_transcripts", "")

            if isinstance(data, list):
                for item in data:
                    transcript_text = item.get("transcript", "")
                    if transcript_text and transcript_text not in UNAVAILABLE_MARKERS:
                        transcripts.append({
                            "title": item.get("title", "Unknown"),
                            "channel": channel,
                            "transcript": transcript_text[:MAX_CHARS_PER_TRANSCRIPT],
                            "source": item.get("source", "unknown"),
                        })
            elif isinstance(data, dict):
                transcript_text = data.get("transcript", "")
                if transcript_text and transcript_text not in UNAVAILABLE_MARKERS:
                    transcripts.append({
                        "title": data.get("title", "Unknown"),
                        "channel": channel,
                        "transcript": transcript_text[:MAX_CHARS_PER_TRANSCRIPT],
                        "source": data.get("source", "unknown"),
                    })
        except (json.JSONDecodeError, KeyError):
            continue

    return transcripts[:MAX_TRANSCRIPTS]


def format_transcripts(transcripts: list[dict]) -> str:
    """Format transcripts into a single text block for Gemini."""
    parts = []
    for i, t in enumerate(transcripts, 1):
        parts.append(f"--- VIDEO {i} | Channel: {t['channel']} | Title: {t['title']} ---\n{t['transcript']}\n")
    return "\n".join(parts)


def get_unique_channels(transcripts: list[dict]) -> list[str]:
    """Get unique channel names."""
    return list(set(t["channel"] for t in transcripts))


def analyze(transcript_dir: str, niche: str, output_dir: str, retries: int = 2) -> dict:
    """Run Gemini analysis on transcripts."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    transcript_path = Path(transcript_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load and merge transcripts
    print(f"Loading transcripts from {transcript_path}...")
    transcripts = load_transcripts(transcript_path)
    if not transcripts:
        print("ERROR: No valid transcripts found")
        sys.exit(1)

    channels = get_unique_channels(transcripts)
    formatted = format_transcripts(transcripts)

    print(f"Loaded {len(transcripts)} transcripts from {len(channels)} channels")
    print(f"Total text: {len(formatted):,} characters")

    # Build prompt
    prompt = ANALYSIS_PROMPT.format(
        niche=niche,
        num_channels=len(channels),
        num_transcripts=len(transcripts),
        transcripts=formatted
    )

    # Call Gemini
    client = genai.Client(api_key=api_key)

    for attempt in range(retries):
        try:
            print(f"Sending to Gemini 2.0 Flash (attempt {attempt + 1})...")
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.7,
                    max_output_tokens=8192,
                )
            )

            result = json.loads(response.text)

            # Save output
            output_file = output_path / "analysis.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"Analysis saved to {output_file}")
            print(f"Course: {result.get('course_title', 'N/A')}")
            print(f"Modules: {len(result.get('modules', []))}")
            total_lessons = sum(len(m.get("lessons", [])) for m in result.get("modules", []))
            print(f"Lessons: {total_lessons}")

            return result

        except (json.JSONDecodeError, Exception) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                print("ERROR: All retries exhausted")
                sys.exit(1)

    return {}


def main():
    parser = argparse.ArgumentParser(description="Analyze YouTube transcripts with Gemini")
    parser.add_argument("--transcripts", "-t", required=True, help="Directory with transcript JSON files")
    parser.add_argument("--niche", "-n", required=True, help="Niche name (e.g., 'productivity')")
    parser.add_argument("--output", "-o", required=True, help="Output directory for analysis.json")
    args = parser.parse_args()

    analyze(args.transcripts, args.niche, args.output)


if __name__ == "__main__":
    main()
