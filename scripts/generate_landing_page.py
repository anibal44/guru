#!/usr/bin/env python3
"""
Guru — Landing Page Generator
Generates a landing page using v0 API (primary) or HTML template (fallback).
No pip dependencies — uses urllib only.
"""

import sys
import os
import json
import argparse
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime

# ─── Niche Color/Font Presets ────────────────────────────────────────────────

NICHE_COLORS = {
    "productivity":      {"primary": "#6366f1", "primary_dark": "#4f46e5", "secondary": "#1e1b4b", "accent": "#a78bfa", "font": "Inter"},
    "cooking":           {"primary": "#ea580c", "primary_dark": "#c2410c", "secondary": "#431407", "accent": "#fb923c", "font": "DM Sans"},
    "personal finance":  {"primary": "#059669", "primary_dark": "#047857", "secondary": "#022c22", "accent": "#34d399", "font": "Plus Jakarta Sans"},
    "fitness":           {"primary": "#dc2626", "primary_dark": "#b91c1c", "secondary": "#450a0a", "accent": "#f87171", "font": "Outfit"},
    "marketing":         {"primary": "#7c3aed", "primary_dark": "#6d28d9", "secondary": "#2e1065", "accent": "#c084fc", "font": "Space Grotesk"},
    "meditation":        {"primary": "#0d9488", "primary_dark": "#0f766e", "secondary": "#042f2e", "accent": "#5eead4", "font": "Nunito"},
    "photography":       {"primary": "#d97706", "primary_dark": "#b45309", "secondary": "#451a03", "accent": "#fbbf24", "font": "Sora"},
    "programming":       {"primary": "#2563eb", "primary_dark": "#1d4ed8", "secondary": "#172554", "accent": "#60a5fa", "font": "JetBrains Mono"},
    "design":            {"primary": "#e11d48", "primary_dark": "#be123c", "secondary": "#4c0519", "accent": "#fb7185", "font": "Satoshi"},
    "business":          {"primary": "#1d4ed8", "primary_dark": "#1e40af", "secondary": "#172554", "accent": "#93c5fd", "font": "Inter"},
}

DEFAULT_COLORS = {"primary": "#6366f1", "primary_dark": "#4f46e5", "secondary": "#1e1b4b", "accent": "#a78bfa", "font": "Inter"}

# ─── Module Emoji Map ────────────────────────────────────────────────────────

MODULE_EMOJIS = ["🎯", "🧱", "⏱️", "🧠", "🚀", "🔄", "💡", "📊", "🔥", "🏆"]

# ─── Pain Point Emojis ───────────────────────────────────────────────────────

PAIN_EMOJIS = ["😤", "😰", "🔥", "📧", "💔", "🔄", "📱", "😓", "🤯", "⏰"]

# ─── Data Loading ────────────────────────────────────────────────────────────

def load_data(outline_path, sales_copy_path=None):
    """Load outline.json and optionally sales-copy.md."""
    with open(outline_path, "r") as f:
        outline = json.load(f)

    sales_copy = None
    if sales_copy_path and os.path.exists(sales_copy_path):
        with open(sales_copy_path, "r") as f:
            sales_copy = f.read()

    return outline, sales_copy


def resolve_colors(niche):
    """Resolve color scheme and font for a niche."""
    niche_lower = niche.lower()
    for key, colors in NICHE_COLORS.items():
        if key in niche_lower or niche_lower in key:
            return colors
    return DEFAULT_COLORS


# ─── v0 API Integration ─────────────────────────────────────────────────────

V0_API_URL = "https://api.v0.dev/v1/chat/completions"
V0_PLATFORM_API = "https://api.v0.dev/v1"
V0_MODEL = "v0-1.5-md"


def build_system_prompt(colors, font):
    """Build the prescriptive system prompt for v0."""
    return f"""You are a world-class landing page designer. Generate a SINGLE, COMPLETE, STANDALONE HTML file.

CRITICAL RULES:
- Output ONLY a single HTML file with ALL CSS inline in a <style> tag
- NO React, NO JSX, NO components, NO imports, NO build steps
- NO external dependencies except ONE Google Fonts link
- Dark theme ONLY (background: #0a0a0a)
- Mobile-first responsive design
- Use CSS custom properties for colors
- Include IntersectionObserver for scroll reveal animations
- Include accordion JS for curriculum and FAQ sections
- The page must be self-contained and work when opened as a local file

COLOR SCHEME (use as CSS custom properties):
--primary: {colors['primary']};
--primary-dark: {colors['primary_dark']};
--secondary: {colors['secondary']};
--accent: {colors['accent']};
--bg: #0a0a0a;
--bg-card: #141414;
--text: #f5f5f5;
--text-muted: #a0a0a0;
--border: #2a2a2a;

FONT: '{font}' from Google Fonts (with system-ui fallback)

REQUIRED SECTIONS (in this exact order):
1. HERO — Full viewport height, gradient-styled title with <span class="highlight"> on key words, subtitle, stats bar (modules/lessons/videos), CTA button linking to #pricing, proof line
2. PAIN POINTS — Section with emoji card grid showing audience pain points, hover effects
3. MODULES — Card grid with module number, emoji icon, title, description hook, lesson count
4. CURRICULUM ACCORDION — Expandable sections per module, first one open by default, shows lesson titles and learning outcomes
5. PRICING — id="pricing", centered card, $97 one-time, feature checklist with checkmarks, CTA button, 30-day guarantee badge
6. FAQ — Accordion style, objection-handling questions and answers
7. FOOTER — Final CTA button linking to #pricing, copyright with current year

DESIGN QUALITY:
- Subtle radial gradient blobs in hero (opacity 0.05-0.08)
- Cards with border: 1px solid var(--border), hover glow effects
- Gradient top-border on cards (3px, primary to accent)
- Scroll-reveal animations (translateY 30px, opacity 0→1)
- Staggered animation delays on card grids
- Professional spacing: sections 100px padding, mobile 72px
- clamp() for responsive typography
- Smooth scroll behavior"""


def build_user_message(outline, sales_copy, niche, total_videos, colors):
    """Build the user message with all course data."""
    course_title = outline.get("course_title", f"Master {niche.title()}")
    course_subtitle = outline.get("course_subtitle", f"The complete {niche} course")
    total_modules = outline.get("total_modules", len(outline.get("modules", [])))
    total_lessons = outline.get("total_lessons", 0)
    pain_points = outline.get("pain_points", [])
    modules = outline.get("modules", [])

    msg = f"""Generate a complete landing page for this course.

COURSE DATA:
- Title: {course_title}
- Subtitle: {course_subtitle}
- Niche: {niche}
- Total Modules: {total_modules}
- Total Lessons: {total_lessons}
- Videos Analyzed: {total_videos}
- Year: {datetime.now().year}

PAIN POINTS:
{json.dumps(pain_points, indent=2)}

MODULES:
{json.dumps(modules, indent=2)}
"""

    if sales_copy:
        # Truncate sales copy to avoid exceeding context
        truncated = sales_copy[:6000] if len(sales_copy) > 6000 else sales_copy
        msg += f"""
SALES COPY (use this for headlines, subheads, CTA text, FAQ answers):
{truncated}
"""

    msg += """
IMPORTANT: Output ONLY the complete HTML file. No explanation, no markdown, just the HTML starting with <!DOCTYPE html>."""

    return msg


def call_v0_api(api_key, system_prompt, user_message, max_tokens=16000, timeout=120):
    """Call v0 API using urllib (no pip deps)."""
    payload = json.dumps({
        "model": V0_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_completion_tokens": max_tokens,
        "stream": False,
    }).encode("utf-8")

    req = Request(
        V0_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    response = urlopen(req, timeout=timeout)
    data = json.loads(response.read().decode("utf-8"))

    # Extract content from OpenAI-compatible response
    content = data["choices"][0]["message"]["content"]
    finish_reason = data["choices"][0].get("finish_reason", "unknown")
    usage = data.get("usage", {})

    return content, finish_reason, usage


def extract_html(content):
    """Extract HTML from v0 response (may be wrapped in markdown fences)."""
    # Try markdown code fence: ```html ... ```
    fence_match = re.search(r"```(?:html)?\s*\n(<!DOCTYPE html>.*?</html>)\s*```", content, re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    # Try raw <!DOCTYPE html>...</html>
    raw_match = re.search(r"(<!DOCTYPE html>.*</html>)", content, re.DOTALL | re.IGNORECASE)
    if raw_match:
        return raw_match.group(1).strip()

    # Content starts with <!doctype
    if content.strip().lower().startswith("<!doctype html>"):
        return content.strip()

    return None


def validate_html(html, course_title):
    """Validate the generated HTML meets minimum requirements."""
    errors = []

    if not html.strip().lower().startswith("<!doctype html>"):
        errors.append("Missing <!DOCTYPE html>")
    if not html.strip().lower().endswith("</html>"):
        errors.append("Missing closing </html>")
    if "<style>" not in html.lower() and "<style " not in html.lower():
        errors.append("No <style> tag found (CSS missing)")
    if 'id="pricing"' not in html.lower():
        errors.append("Missing id='pricing' (CTA target)")
    if html.lower().count("<section") < 3:
        errors.append(f"Only {html.lower().count('<section')} <section> tags (need 3+)")

    size = len(html.encode("utf-8"))
    if size < 5000:
        errors.append(f"HTML too small ({size} bytes, min 5KB)")
    if size > 200000:
        errors.append(f"HTML too large ({size} bytes, max 200KB)")

    # Check course title is embedded (fuzzy — first 3 words)
    title_words = course_title.split()[:3]
    title_check = " ".join(title_words).lower()
    if title_check and title_check not in html.lower():
        errors.append(f"Course title not found in HTML (looked for '{title_check}')")

    # Check for React/JSX indicators
    react_indicators = ["import React", "from 'react'", 'from "react"', "useState(", "useEffect(", "className={", "export default"]
    for indicator in react_indicators:
        if indicator in html:
            errors.append(f"React/JSX detected: '{indicator}'")
            break

    return errors


def try_v0_generation(api_key, outline, sales_copy, niche, total_videos, colors, font, max_tokens=16000):
    """Attempt to generate landing page via v0 API. Returns (html, errors) or (None, errors)."""
    system_prompt = build_system_prompt(colors, font)
    user_message = build_user_message(outline, sales_copy, niche, total_videos, colors)

    try:
        print(f"[v0] Calling v0 API (model={V0_MODEL}, max_tokens={max_tokens})...")
        start = time.time()
        content, finish_reason, usage = call_v0_api(api_key, system_prompt, user_message, max_tokens=max_tokens)
        elapsed = time.time() - start
        print(f"[v0] Response received in {elapsed:.1f}s (finish_reason={finish_reason})")

        if usage:
            print(f"[v0] Tokens: {usage.get('prompt_tokens', '?')} in, {usage.get('completion_tokens', '?')} out")

        html = extract_html(content)
        if not html:
            return None, ["Could not extract HTML from v0 response"]

        course_title = outline.get("course_title", niche.title())
        errors = validate_html(html, course_title)

        if errors:
            return html, errors

        return html, []

    except HTTPError as e:
        code = e.code
        if code == 429:
            return None, [f"Rate limited (HTTP 429)"]
        return None, [f"HTTP {code}: {e.reason}"]
    except URLError as e:
        return None, [f"Connection error: {e.reason}"]
    except TimeoutError:
        return None, ["Request timed out (120s)"]
    except Exception as e:
        return None, [f"Unexpected error: {e}"]


# ─── v0 Platform Publishing ──────────────────────────────────────────────────


def publish_to_v0(api_key, outline, sales_copy, niche, total_videos):
    """Publish landing page to v0 Platform and return shareable demo URL.

    Uses v0 Platform API:
    1. POST /v1/projects — create project
    2. POST /v1/chats — create chat with course data (v0 generates a full Next.js app)
    Returns (demo_url, editor_url) or (None, None) on failure.
    """
    # Build compact course data message for v0 Platform
    course_title = outline.get("course_title", f"Master {niche.title()}")
    course_subtitle = outline.get("course_subtitle", f"The complete {niche} course")
    total_modules = outline.get("total_modules", len(outline.get("modules", [])))
    total_lessons = outline.get("total_lessons", 0)
    pain_points = outline.get("pain_points", [])
    modules = outline.get("modules", [])

    # Compact module summaries (avoid timeout from too much data)
    module_lines = []
    for m in modules:
        lesson_count = len(m.get("lessons", []))
        module_lines.append(f"- Module {m['number']}: {m['title']} ({lesson_count} lessons)")

    pain_lines = "\n".join(f"- {p}" for p in pain_points[:8])
    module_text = "\n".join(module_lines)

    sales_excerpt = ""
    if sales_copy:
        sales_excerpt = f"\n\nSALES COPY EXCERPT (use for headlines, CTAs, tone):\n{sales_copy[:3000]}"

    message = f"""Build a premium dark-themed landing page for an online course.

COURSE: {course_title}
SUBTITLE: {course_subtitle}
NICHE: {niche}
PRICE: $97 one-time
MODULES: {total_modules} | LESSONS: {total_lessons} | VIDEOS ANALYZED: {total_videos}

PAIN POINTS:
{pain_lines}

MODULES:
{module_text}
{sales_excerpt}

REQUIREMENTS:
- Dark theme (#0a0a0a background)
- 7 sections: Hero (full viewport, stats bar, CTA), Pain Points (emoji cards), Modules (card grid), Curriculum (accordion), Pricing ($97, guarantee badge), FAQ (accordion), Footer
- Gradient accents, scroll animations, mobile responsive
- 30-day money-back guarantee
- CTA buttons link to #pricing section
- Professional, premium feel — not generic"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Step 1: Create project
    try:
        print("[v0 Platform] Creating project...")
        project_payload = json.dumps({
            "name": f"Guru {niche.title()} Landing Page",
        }).encode("utf-8")

        req = Request(
            f"{V0_PLATFORM_API}/projects",
            data=project_payload,
            headers=headers,
            method="POST",
        )
        resp = urlopen(req, timeout=30)
        project = json.loads(resp.read().decode("utf-8"))
        project_id = project["id"]
        print(f"[v0 Platform] Project created: {project_id}")
    except Exception as e:
        print(f"[v0 Platform] Failed to create project: {e}")
        return None, None

    # Step 2: Create chat with course data (v0 generates full app)
    try:
        print("[v0 Platform] Generating page (this takes 2-4 minutes)...")
        chat_payload = json.dumps({
            "message": message,
            "projectId": project_id,
        }).encode("utf-8")

        req = Request(
            f"{V0_PLATFORM_API}/chats",
            data=chat_payload,
            headers=headers,
            method="POST",
        )

        start = time.time()
        resp = urlopen(req, timeout=300)
        elapsed = time.time() - start
        chat = json.loads(resp.read().decode("utf-8"))

        chat_id = chat.get("id", "unknown")
        demo_url = None
        editor_url = f"https://v0.app/chat/{chat_id}"

        # Extract demo URL from latestVersion
        latest = chat.get("latestVersion", {})
        demo_url = latest.get("demoUrl")

        if demo_url:
            print(f"[v0 Platform] Page generated in {elapsed:.0f}s")
            print(f"[v0 Platform] Demo URL:   {demo_url}")
            print(f"[v0 Platform] Editor URL: {editor_url}")
            return demo_url, editor_url
        else:
            print(f"[v0 Platform] Chat created but no demoUrl in response")
            print(f"[v0 Platform] Editor URL: {editor_url}")
            return None, editor_url

    except TimeoutError:
        print("[v0 Platform] Chat creation timed out (300s)")
        return None, None
    except Exception as e:
        print(f"[v0 Platform] Failed to create chat: {e}")
        return None, None


# ─── Template Fallback ───────────────────────────────────────────────────────

def generate_pain_cards(pain_points):
    """Generate HTML pain point cards."""
    cards = []
    for i, pain in enumerate(pain_points[:8]):
        emoji = PAIN_EMOJIS[i % len(PAIN_EMOJIS)]
        delay = (i % 5) + 1
        cards.append(f'''            <div class="pain-card reveal reveal-delay-{delay}">
                <div class="pain-icon">{emoji}</div>
                <p>{pain}</p>
            </div>''')
    return "\n".join(cards)


def generate_module_cards(modules):
    """Generate HTML module cards."""
    cards = []
    for i, mod in enumerate(modules):
        emoji = MODULE_EMOJIS[i % len(MODULE_EMOJIS)]
        delay = (i % 5) + 1
        lesson_count = len(mod.get("lessons", []))
        cards.append(f'''            <div class="module-card reveal reveal-delay-{delay}">
                <span class="module-number">Module {mod["number"]}</span>
                <span class="module-icon">{emoji}</span>
                <h3>{mod["title"]}</h3>
                <p>{mod.get("description", "")}</p>
                <div class="module-lessons-count">{lesson_count} lessons</div>
            </div>''')
    return "\n".join(cards)


def generate_curriculum_accordion(modules):
    """Generate HTML curriculum accordion."""
    items = []
    for mod in modules:
        lessons_html = []
        for lesson in mod.get("lessons", []):
            lessons_html.append(f'''                        <li class="lesson-item">
                            <span class="lesson-num">{mod["number"]}.{lesson["number"]}</span>
                            <div class="lesson-info">
                                <h4>{lesson["title"]}</h4>
                                <p>{lesson.get("learning_outcome", "")}</p>
                            </div>
                        </li>''')

        items.append(f'''            <div class="accordion-item">
                <button class="accordion-trigger">
                    <span><span class="mod-label">Module {mod["number"]}</span> {mod["title"]}</span>
                    <span class="chevron">&#9660;</span>
                </button>
                <div class="accordion-content">
                    <div class="accordion-body">
                        <ul class="lesson-list">
{chr(10).join(lessons_html)}
                        </ul>
                    </div>
                </div>
            </div>''')
    return "\n".join(items)


def generate_faq_items(sales_copy, niche, outline):
    """Generate FAQ items from sales copy or generic defaults."""
    default_faqs = [
        ("Who is this course for?", f"This course is designed for anyone who wants to master {niche} — whether you're a complete beginner or have some experience. The curriculum was built from research on hundreds of expert videos, so it covers both foundational concepts and advanced strategies."),
        ("How long do I have access?", "Lifetime access. Once you enroll, you can go through the material at your own pace, revisit any module, and access all future updates at no extra cost."),
        ("What if it's not for me?", "No risk. We offer a 30-day money-back guarantee, no questions asked. If the course doesn't deliver value, you get a full refund."),
        ("How is this different from free YouTube content?", f"YouTube gives you fragments. This course gives you a complete, structured system. We analyzed {outline.get('total_lessons', 20)}+ lessons worth of expert content and organized it into a step-by-step curriculum — no fluff, no searching, no piecing things together."),
        ("Do I need any prior experience?", f"No. Module 1 starts with the fundamentals and each module builds on the last. By the end, you'll have a complete {niche} system."),
    ]

    items = []
    for q, a in default_faqs:
        items.append(f'''            <div class="accordion-item">
                <button class="accordion-trigger">
                    <span>{q}</span>
                    <span class="chevron">&#9660;</span>
                </button>
                <div class="accordion-content">
                    <div class="accordion-body">
                        <p>{a}</p>
                    </div>
                </div>
            </div>''')
    return "\n".join(items)


def fallback_template(outline, sales_copy, niche, total_videos, colors, font):
    """Generate landing page using the HTML template with placeholder replacement."""
    template_path = Path(__file__).parent.parent / "templates" / "landing-page" / "index.html"

    if not template_path.exists():
        print(f"ERROR: Template not found at {template_path}")
        sys.exit(1)

    html = template_path.read_text()

    course_title = outline.get("course_title", f"Master {niche.title()}")
    course_subtitle = outline.get("course_subtitle", f"The complete {niche} course")
    total_modules = outline.get("total_modules", len(outline.get("modules", [])))
    total_lessons = outline.get("total_lessons", 0)
    pain_points = outline.get("pain_points", [])
    modules = outline.get("modules", [])

    # Build title HTML with highlight on last 2 words
    title_words = course_title.split()
    if len(title_words) > 2:
        plain = " ".join(title_words[:-2])
        highlight = " ".join(title_words[-2:])
        title_html = f'{plain} <span class="highlight">{highlight}</span>'
    else:
        title_html = f'<span class="highlight">{course_title}</span>'

    # Google Fonts URL-safe font name
    font_url = font.replace(" ", "+")

    # Replace all placeholders
    replacements = {
        "{{COURSE_TITLE_HTML}}": title_html,
        "{{COURSE_TITLE}}": course_title,
        "{{COURSE_SUBTITLE}}": course_subtitle,
        "{{NICHE}}": niche,
        "{{NICHE_CAPITALIZED}}": niche.title(),
        "{{TOTAL_MODULES}}": str(total_modules),
        "{{TOTAL_LESSONS}}": str(total_lessons),
        "{{TOTAL_VIDEOS}}": str(total_videos),
        "{{HERO_IMAGE}}": "assets/hero.jpg",
        "{{PRIMARY_COLOR}}": colors["primary"],
        "{{PRIMARY_DARK}}": colors["primary_dark"],
        "{{SECONDARY_COLOR}}": colors["secondary"],
        "{{ACCENT_COLOR}}": colors["accent"],
        "{{FONT_FAMILY}}": font_url,
        "{{YEAR}}": str(datetime.now().year),
        "{{PAIN_POINTS}}": generate_pain_cards(pain_points),
        "{{MODULE_CARDS}}": generate_module_cards(modules),
        "{{CURRICULUM_ACCORDION}}": generate_curriculum_accordion(modules),
        "{{FAQ_ITEMS}}": generate_faq_items(sales_copy, niche, outline),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate landing page (v0 API + template fallback)")
    parser.add_argument("--outline", "-o", required=True, help="Path to outline.json")
    parser.add_argument("--sales-copy", "-s", default=None, help="Path to sales-copy.md (optional)")
    parser.add_argument("--niche", "-n", required=True, help="Niche name")
    parser.add_argument("--total-videos", "-v", type=int, default=250, help="Total videos analyzed (default: 250)")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--force-fallback", action="store_true", help="Skip v0, use template directly")
    parser.add_argument("--publish", action="store_true", help="Publish to v0 Platform for shareable demo URL")
    args = parser.parse_args()

    # Load data
    outline, sales_copy = load_data(args.outline, args.sales_copy)
    colors = resolve_colors(args.niche)
    font = colors.pop("font", "Inter")
    # Restore font in colors dict for reference
    colors["font"] = font

    total_videos = args.total_videos
    niche = args.niche

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = None
    method = None

    # ─── PRIMARY: v0 API ─────────────────────────────────────────────────
    api_key = os.environ.get("V0_API_KEY")

    if args.force_fallback:
        print("[INFO] --force-fallback set, skipping v0 API")
    elif not api_key:
        print("[INFO] V0_API_KEY not set, skipping v0 API")
    else:
        # Attempt 1: standard max_tokens
        html, errors = try_v0_generation(api_key, outline, sales_copy, niche, total_videos, colors, font, max_tokens=16000)

        if html and not errors:
            method = "v0"
            print("[v0] Generation successful!")

        elif html and errors:
            # Got HTML but validation failed
            react_error = any("React" in e or "JSX" in e for e in errors)
            truncation_likely = any("too small" in e.lower() or "missing closing" in e.lower() for e in errors)

            print(f"[v0] Validation issues: {', '.join(errors)}")

            if react_error:
                print("[v0] React/JSX detected — retrying with stronger constraints...")
                # Don't retry for React — v0 tends to repeat. Go to fallback.
                html = None
            elif truncation_likely:
                print("[v0] Possible truncation — retrying with max_tokens=32000...")
                html, errors = try_v0_generation(api_key, outline, sales_copy, niche, total_videos, colors, font, max_tokens=32000)
                if html and not errors:
                    method = "v0"
                    print("[v0] Retry successful!")
                else:
                    print(f"[v0] Retry failed: {', '.join(errors) if errors else 'no HTML'}")
                    html = None
            else:
                # Non-critical validation issues — use the HTML anyway if it has basic structure
                if html.strip().lower().startswith("<!doctype html>") and "</html>" in html.lower():
                    method = "v0 (with warnings)"
                    print(f"[v0] Using HTML despite warnings: {', '.join(errors)}")
                else:
                    html = None
        else:
            print(f"[v0] Failed: {', '.join(errors) if errors else 'no response'}")

            # Attempt 2: retry with higher token limit
            if errors and not any("429" in e for e in errors):
                print("[v0] Retrying with max_tokens=32000...")
                html, errors = try_v0_generation(api_key, outline, sales_copy, niche, total_videos, colors, font, max_tokens=32000)
                if html and not errors:
                    method = "v0"
                    print("[v0] Retry successful!")
                elif html and not any("React" in e or "JSX" in e for e in errors):
                    if html.strip().lower().startswith("<!doctype html>") and "</html>" in html.lower():
                        method = "v0 (with warnings)"
                        print(f"[v0] Using retry HTML despite warnings: {', '.join(errors)}")
                    else:
                        html = None
                else:
                    html = None

    # ─── FALLBACK: Template ──────────────────────────────────────────────
    if not html:
        print("[FALLBACK] Using HTML template...")
        # Remove font key for fallback (it uses font_url separately)
        fb_colors = {k: v for k, v in colors.items() if k != "font"}
        fb_colors["font"] = font
        html = fallback_template(outline, sales_copy, niche, total_videos, fb_colors, font)
        method = "template"
        print("[FALLBACK] Template generation complete")

    # ─── Write output ────────────────────────────────────────────────────
    output_path.write_text(html, encoding="utf-8")
    size_kb = len(html.encode("utf-8")) / 1024

    print()
    print(f"{'=' * 50}")
    print(f"Landing page generated successfully!")
    print(f"  Method:  {method}")
    print(f"  Output:  {output_path}")
    print(f"  Size:    {size_kb:.1f} KB")
    print(f"{'=' * 50}")

    # ─── Optional: Publish to v0 Platform ─────────────────────────────
    if args.publish:
        api_key = os.environ.get("V0_API_KEY")
        if not api_key:
            print("\n[PUBLISH] V0_API_KEY not set — skipping v0 Platform publish")
        else:
            print(f"\n{'=' * 50}")
            print("Publishing to v0 Platform...")
            print(f"{'=' * 50}")
            demo_url, editor_url = publish_to_v0(api_key, outline, sales_copy, niche, total_videos)
            if demo_url:
                print(f"\n{'=' * 50}")
                print(f"v0 Platform published!")
                print(f"  Demo URL:   {demo_url}")
                print(f"  Editor URL: {editor_url}")
                print(f"{'=' * 50}")
            elif editor_url:
                print(f"\n[PUBLISH] Editor created but no demo URL: {editor_url}")
            else:
                print("\n[PUBLISH] v0 Platform publish failed — static HTML is still available")


if __name__ == "__main__":
    main()
