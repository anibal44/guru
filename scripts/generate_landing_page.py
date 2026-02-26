#!/usr/bin/env python3
"""
Guru — Landing Page Generator
Generates a local HTML landing page from template, and optionally publishes
a premium version to v0 Platform (shareable Next.js app).

No pip dependencies — uses urllib only.

Usage:
    # Local HTML only (always works, no API key needed):
    python3 generate_landing_page.py --outline outline.json --niche "productivity" --output index.html

    # Local HTML + v0 Platform publish (shareable demo URL):
    python3 generate_landing_page.py --outline outline.json --niche "productivity" --output index.html --publish
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path
from urllib.request import Request, urlopen
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

MODULE_EMOJIS = ["🎯", "🧱", "⏱️", "🧠", "🚀", "🔄", "💡", "📊", "🔥", "🏆"]
PAIN_EMOJIS = ["😤", "😰", "🔥", "📧", "💔", "🔄", "📱", "😓", "🤯", "⏰"]

V0_PLATFORM_API = "https://api.v0.dev/v1"

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


# ─── Template Generator (local HTML) ────────────────────────────────────────


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


# ─── v0 Platform Publishing ──────────────────────────────────────────────────


def publish_to_v0(api_key, outline, sales_copy, niche, total_videos):
    """Publish to v0 Platform — generates a full Next.js app with shareable demo URL.

    Uses v0 Platform API:
    1. POST /v1/projects — create project
    2. POST /v1/chats — send course data, v0 builds a complete app
    Returns (demo_url, editor_url) or (None, None) on failure.
    """
    course_title = outline.get("course_title", f"Master {niche.title()}")
    course_subtitle = outline.get("course_subtitle", f"The complete {niche} course")
    total_modules = outline.get("total_modules", len(outline.get("modules", [])))
    total_lessons = outline.get("total_lessons", 0)
    pain_points = outline.get("pain_points", [])
    modules = outline.get("modules", [])

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

    # Step 2: Create chat with course data (v0 generates full Next.js app)
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
        editor_url = f"https://v0.app/chat/{chat_id}"

        demo_url = chat.get("latestVersion", {}).get("demoUrl")

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


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generate landing page (template + v0 Platform publish)")
    parser.add_argument("--outline", "-o", required=True, help="Path to outline.json")
    parser.add_argument("--sales-copy", "-s", default=None, help="Path to sales-copy.md (optional)")
    parser.add_argument("--niche", "-n", required=True, help="Niche name")
    parser.add_argument("--total-videos", "-v", type=int, default=250, help="Total videos analyzed (default: 250)")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--publish", action="store_true", help="Publish to v0 Platform for shareable demo URL (requires V0_API_KEY)")
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

    # ─── Generate local HTML from template ────────────────────────────
    print("[Template] Generating local HTML...")
    html = generate_template(outline, sales_copy, niche, total_videos, colors, font)
    output_path.write_text(html, encoding="utf-8")
    size_kb = len(html.encode("utf-8")) / 1024

    print()
    print(f"{'=' * 50}")
    print(f"Local landing page generated!")
    print(f"  Method:  template")
    print(f"  Output:  {output_path}")
    print(f"  Size:    {size_kb:.1f} KB")
    print(f"{'=' * 50}")

    # ─── Publish to v0 Platform (premium shareable version) ───────────
    if args.publish:
        api_key = os.environ.get("V0_API_KEY")
        if not api_key:
            print("\n[PUBLISH] V0_API_KEY not set — skipping v0 Platform publish")
        else:
            print(f"\n{'=' * 50}")
            print("Publishing to v0 Platform (premium version)...")
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
                print("\n[PUBLISH] v0 Platform publish failed — local HTML is still available")


if __name__ == "__main__":
    main()
