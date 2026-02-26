#!/usr/bin/env python3
"""
Guru — Hero Image Generator
Generates a niche-appropriate hero image using Gemini image generation.
"""

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


MODEL = "gemini-2.0-flash-preview-image-generation"

NICHE_STYLES = {
    "productivity": "minimalist workspace with organized desk, morning light, clean lines, professional",
    "cooking": "beautiful artisanal kitchen, warm tones, fresh ingredients, steam rising from dishes",
    "personal finance": "elegant financial planning scene, modern office, growth charts, wealth building",
    "fitness": "dynamic athletic training environment, energy, determination, modern gym",
    "marketing": "creative digital marketing workspace, multiple screens, data dashboards, growth",
    "photography": "stunning camera gear with beautiful landscape backdrop, golden hour lighting",
    "meditation": "serene zen space, soft natural light, peaceful atmosphere, mindfulness",
    "programming": "futuristic coding environment, multiple monitors, clean code, tech aesthetic",
    "design": "creative studio with design tools, color palettes, modern workspace, artistic",
    "business": "professional executive environment, boardroom, city skyline, success",
}

IMAGE_PROMPT = """Create a premium, cinematic hero image for an online course about {niche}.

Style: {style}

Requirements:
- 16:9 aspect ratio landscape orientation
- Rich, vibrant colors with professional color grading
- Depth of field with bokeh effect in background
- No text, no logos, no watermarks, no people's faces
- Premium stock photo quality — NOT generic, NOT AI-looking
- Warm, inviting, aspirational mood
- Could be used as a course header on a $97 product page

The image should make someone feel excited about mastering {niche}."""


def get_style(niche: str) -> str:
    """Get style description for a niche, with fallback."""
    niche_lower = niche.lower()
    for key, style in NICHE_STYLES.items():
        if key in niche_lower or niche_lower in key:
            return style
    return f"professional, modern, premium aesthetic related to {niche}, aspirational"


def generate_hero(niche: str, output_path: str, retries: int = 2) -> str:
    """Generate hero image and save to output path."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    style = get_style(niche)
    prompt = IMAGE_PROMPT.format(niche=niche, style=style)

    client = genai.Client(api_key=api_key)

    for attempt in range(retries):
        try:
            print(f"Generating hero image for '{niche}' (attempt {attempt + 1})...")
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )

            # Extract image from response
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_data = part.inline_data.data
                    with open(output, "wb") as f:
                        f.write(image_data)
                    print(f"Hero image saved to {output}")
                    print(f"Size: {len(image_data):,} bytes")
                    return str(output)

            print(f"Attempt {attempt + 1}: No image in response")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")

    # Fallback: check for pre-generated images
    fallback_dir = Path(__file__).parent.parent / "templates" / "fallback"
    fallbacks = list(fallback_dir.glob("*.jpg")) + list(fallback_dir.glob("*.png"))
    if fallbacks:
        import shutil
        fallback = fallbacks[0]
        shutil.copy2(fallback, output)
        print(f"Using fallback image: {fallback.name}")
        return str(output)

    print("ERROR: Could not generate hero image and no fallback available")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate hero image for course landing page")
    parser.add_argument("--niche", "-n", required=True, help="Niche name")
    parser.add_argument("--output", "-o", required=True, help="Output file path (e.g., hero.jpg)")
    args = parser.parse_args()

    generate_hero(args.niche, args.output)


if __name__ == "__main__":
    main()
