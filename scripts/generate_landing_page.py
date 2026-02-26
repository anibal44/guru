#!/usr/bin/env python3
"""
Guru — Landing Page Generator
v0 AI-powered landing page generation with template fallback.

Primary: v0 Chat Completions API (v0-1.5-md) — generates a complete standalone HTML page.
Fallback: Local template with placeholder replacement (no API needed).

Timeout: 5 minutes for v0. If exceeded, falls back to template automatically.
No pip dependencies — uses urllib only.

Usage:
    python3 generate_landing_page.py --outline outline.json --niche "productivity" --output index.html
    python3 generate_landing_page.py --outline outline.json --niche "productivity" --output index.html --template-only
"""

import sys
import os
import json
import re
import argparse
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime

# ─── API Key (env var only — GitHub blocks hardcoded Vercel tokens) ───────────

V0_API_KEY = os.environ.get("V0_API_KEY", "")
V0_API_URL = "https://api.v0.dev/v1/chat/completions"
V0_MODEL = "v0-1.5-md"
V0_TIMEOUT = 300  # 5 minutes

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

MODULE_EMOJIS = ["🎯", "🧱", "⏱️", "🧠", "🚀", "🔄", "💡", "📊", "🔥", "🏆"]
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
            return dict(colors)
    return dict(DEFAULT_COLORS)


# ─── v0 AI Generation (PRIMARY) ─────────────────────────────────────────────


def build_v0_prompt(outline, sales_copy, niche, total_videos, colors, font):
    """Build the system + user prompt for v0 to generate a landing page."""
    course_title = outline.get("course_title", f"Master {niche.title()}")
    course_subtitle = outline.get("course_subtitle", f"The complete {niche} course")
    total_modules = outline.get("total_modules", len(outline.get("modules", [])))
    total_lessons = outline.get("total_lessons", 0)
    pain_points = outline.get("pain_points", [])
    modules = outline.get("modules", [])

    # Build module data
    module_data = []
    for m in modules:
        lessons = []
        for les in m.get("lessons", []):
            lessons.append(f"  - {m['number']}.{les['number']}: {les['title']}")
        module_data.append(
            f"Module {m['number']}: {m['title']} ({len(m.get('lessons', []))} lessons)\n"
            + "\n".join(lessons)
        )

    pain_text = "\n".join(f"- {p}" for p in pain_points[:8])
    modules_text = "\n\n".join(module_data)

    sales_section = ""
    if sales_copy:
        # Take first ~2500 chars of sales copy for headlines/tone
        sales_section = f"""

SALES COPY (use for headlines, subheadlines, CTA text, and tone of voice):
{sales_copy[:2500]}"""

    system_prompt = f"""You are an expert web designer. Generate a SINGLE, COMPLETE, STANDALONE HTML file for a premium dark-themed course landing page.

CRITICAL REQUIREMENTS:
- Output ONLY valid HTML. No markdown, no explanation, no React, no JSX, no components.
- Single HTML file with ALL CSS inline in a <style> tag and ALL JS inline in a <script> tag.
- NO external dependencies except Google Fonts.
- Dark theme: background #0a0a0a, cards #141414, text #f5f5f5.
- Mobile-first responsive design.
- Smooth scroll behavior, IntersectionObserver reveal animations.

COLOR SCHEME:
- Primary: {colors['primary']}
- Primary Dark: {colors['primary_dark']}
- Secondary: {colors['secondary']}
- Accent: {colors['accent']}
- Google Font: {font}

PAGE STRUCTURE (7 sections, in this exact order):

1. HERO — Full viewport height. Course title with gradient highlight on last 2 words. Subtitle below. Stats bar showing "{total_modules} Modules", "{total_lessons} Lessons", "{total_videos}+ Videos Analyzed". Primary CTA button "Get Instant Access →" linking to #pricing. Hero image placeholder (assets/hero.jpg).

2. PAIN POINTS — Section title "Sound Familiar?". Grid of emoji cards showing audience pain points. Each card has an emoji icon and text.

3. MODULES — Section title "What You'll Learn". Card grid with module number, emoji icon, title, description, lesson count badge. Gradient top border on hover.

4. CURRICULUM — Section title "Full Curriculum". Expandable accordion per module. First module open by default. Each shows lesson number, title, and learning outcome. Chevron rotates on toggle.

5. PRICING — Section with id="pricing". Single pricing card: "$97" large, "one-time payment" subtitle, feature checklist with check marks, "Get Instant Access" CTA button, "30-Day Money-Back Guarantee" badge below.

6. FAQ — Accordion with 5 questions. Include: "Who is this for?", "How is this different from free YouTube?", "How long do I have access?", "What if it's not for me?", "Do I need prior experience?".

7. FOOTER — Final CTA "Ready to Start?" with button, copyright © {datetime.now().year}.

ANIMATIONS:
- Use IntersectionObserver to add "revealed" class when elements enter viewport.
- Staggered reveal delays (reveal-delay-1 through reveal-delay-5).
- Accordion toggle with smooth height transition.
- Button hover: translateY(-2px) + enhanced shadow.
- Cards hover: translateY(-4px) + border color change.

IMPORTANT:
- Start with <!DOCTYPE html>
- End with </html>
- Include <meta charset="UTF-8"> and <meta name="viewport">
- The output must be ONLY the HTML file content, nothing else."""

    user_message = f"""Generate the landing page for this course:

COURSE TITLE: {course_title}
SUBTITLE: {course_subtitle}
NICHE: {niche}
PRICE: $97 one-time payment
GUARANTEE: 30-day money-back, no questions asked

PAIN POINTS:
{pain_text}

MODULES AND LESSONS:
{modules_text}
{sales_section}

Generate the complete HTML file now. Output ONLY the HTML — no markdown fences, no explanation."""

    return system_prompt, user_message


def extract_html(content):
    """Extract HTML from v0 response. Handles markdown fences or raw HTML."""
    # Try markdown code fence: ```html ... ```
    match = re.search(r"```html\s*\n(.*?)```", content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try any code fence: ``` ... ```
    match = re.search(r"```\s*\n(.*?)```", content, re.DOTALL)
    if match:
        inner = match.group(1).strip()
        if inner.lower().startswith("<!doctype") or inner.lower().startswith("<html"):
            return inner

    # Raw HTML (starts with doctype or html tag)
    content_stripped = content.strip()
    if content_stripped.lower().startswith("<!doctype") or content_stripped.lower().startswith("<html"):
        return content_stripped

    return None


def validate_html(html, course_title):
    """Basic validation that the HTML is a complete landing page."""
    errors = []
    html_lower = html.lower()

    if not html_lower.startswith("<!doctype html>"):
        errors.append("Missing <!DOCTYPE html>")
    if "</html>" not in html_lower:
        errors.append("Missing </html>")
    if "<style" not in html_lower:
        errors.append("No <style> tag (CSS missing)")
    if 'id="pricing"' not in html_lower and "id='pricing'" not in html_lower:
        errors.append("No #pricing section (CTA target missing)")
    if html_lower.count("<section") < 3:
        errors.append(f"Only {html_lower.count('<section')} sections (need 3+)")

    size_kb = len(html.encode("utf-8")) / 1024
    if size_kb < 5:
        errors.append(f"Too small ({size_kb:.0f}KB — likely truncated)")
    if size_kb > 200:
        errors.append(f"Too large ({size_kb:.0f}KB)")

    # Check for React/JSX contamination
    if "import react" in html_lower or "from 'react'" in html_lower or "jsx" in html_lower:
        errors.append("Contains React/JSX (need plain HTML)")

    return errors


def try_v0_generation(outline, sales_copy, niche, total_videos, colors, font, max_tokens=16000):
    """Call v0 API to generate landing page HTML. Returns HTML string or None."""
    system_prompt, user_message = build_v0_prompt(outline, sales_copy, niche, total_videos, colors, font)

    payload = json.dumps({
        "model": V0_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_completion_tokens": max_tokens,
        "stream": False,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {V0_API_KEY}",
    }

    req = Request(V0_API_URL, data=payload, headers=headers, method="POST")

    start = time.time()
    try:
        resp = urlopen(req, timeout=V0_TIMEOUT)
        data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"   [v0] HTTP {e.code}: {body[:200]}")
        if e.code == 429:
            print("   [v0] Rate limited — falling back to template")
        return None
    except (URLError, TimeoutError, OSError) as e:
        elapsed = time.time() - start
        print(f"   [v0] Request failed after {elapsed:.0f}s: {e}")
        return None

    elapsed = time.time() - start

    # Extract content from response
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print(f"   [v0] Unexpected response structure")
        return None

    finish_reason = data.get("choices", [{}])[0].get("finish_reason", "unknown")
    usage = data.get("usage", {})
    tokens_out = usage.get("completion_tokens", 0)

    print(f"   [v0] Response: {elapsed:.0f}s, {tokens_out} tokens, finish={finish_reason}")

    # Check for truncation
    if finish_reason == "length":
        print(f"   [v0] Output truncated at {max_tokens} tokens")
        return None  # Caller can retry with higher max_tokens

    # Extract HTML
    html = extract_html(content)
    if not html:
        print(f"   [v0] Could not extract HTML from response")
        print(f"   [v0] First 200 chars: {content[:200]}")
        return None

    # Validate
    course_title = outline.get("course_title", "")
    errors = validate_html(html, course_title)
    if errors:
        print(f"   [v0] Validation errors: {'; '.join(errors)}")
        # Only fail on critical errors
        critical = [e for e in errors if "React" in e or "truncated" in e or "Missing <!DOCTYPE" in e]
        if critical:
            return None
        print(f"   [v0] Non-critical — using anyway")

    return html


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


def generate_template(outline, sales_copy, niche, total_videos, colors, font):
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

    font_url = font.replace(" ", "+")

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
    parser = argparse.ArgumentParser(description="Generate landing page (v0 AI primary, template fallback)")
    parser.add_argument("--outline", "-o", required=True, help="Path to outline.json")
    parser.add_argument("--sales-copy", "-s", default=None, help="Path to sales-copy.md (optional)")
    parser.add_argument("--niche", "-n", required=True, help="Niche name")
    parser.add_argument("--total-videos", "-v", type=int, default=250, help="Total videos analyzed (default: 250)")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--template-only", action="store_true", help="Skip v0, use template directly")
    args = parser.parse_args()

    # Load data
    outline, sales_copy = load_data(args.outline, args.sales_copy)
    colors = resolve_colors(args.niche)
    font = colors.pop("font", "Inter")
    colors["font"] = font

    total_videos = args.total_videos
    niche = args.niche

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    method = "template"
    html = None

    # ─── PRIMARY: v0 AI Generation ──────────────────────────────────
    if not args.template_only and V0_API_KEY:
        print("[v0] Generating landing page with AI (5 min timeout)...")
        html = try_v0_generation(outline, sales_copy, niche, total_videos, colors, font)

        # Retry with higher token limit if truncated
        if html is None:
            print("[v0] Retrying with higher token limit (32K)...")
            html = try_v0_generation(outline, sales_copy, niche, total_videos, colors, font, max_tokens=32000)

        if html:
            method = "v0"
            print("[v0] Success — AI-generated landing page")
        else:
            print("[v0] Failed — falling back to template")
    elif not V0_API_KEY:
        print("[v0] No API key — using template")
    else:
        print("[Template] --template-only flag set")

    # ─── FALLBACK: Template ──────────────────────────────────────────
    if html is None:
        print("[Template] Generating from template...")
        html = generate_template(outline, sales_copy, niche, total_videos, colors, font)
        method = "template"

    # Write output
    output_path.write_text(html, encoding="utf-8")
    size_kb = len(html.encode("utf-8")) / 1024

    print()
    print(f"{'=' * 50}")
    print(f"Landing page generated!")
    print(f"  Method:  {method}")
    print(f"  Output:  {output_path}")
    print(f"  Size:    {size_kb:.1f} KB")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
