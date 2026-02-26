#!/usr/bin/env python3
"""
Guru — Course Outline Generator
Formats Gemini analysis into readable outline (JSON + Markdown).
Pure formatting — no API calls.
"""

import json
import sys
import argparse
from pathlib import Path


def generate_outline(analysis_path: str, output_dir: str) -> tuple[dict, str]:
    """Generate outline.json and outline.md from analysis.json."""
    analysis_file = Path(analysis_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load analysis
    with open(analysis_file, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    # Build outline JSON (structured for LP template — no creator attribution)
    outline = {
        "course_title": analysis.get("course_title", "Untitled Course"),
        "course_subtitle": analysis.get("course_subtitle", ""),
        "target_audience": analysis.get("target_audience", ""),
        "total_modules": len(analysis.get("modules", [])),
        "total_lessons": sum(len(m.get("lessons", [])) for m in analysis.get("modules", [])),
        "pain_points": analysis.get("pain_points", []),
        "modules": [],
        "frameworks": analysis.get("frameworks", []),
    }

    # Collect all source creators (internal only — for sources-reference.md)
    all_creators = set()
    for topic in analysis.get("core_topics", []):
        all_creators.update(topic.get("source_creators", []))
    for module in analysis.get("modules", []):
        for lesson in module.get("lessons", []):
            all_creators.update(lesson.get("source_creators", []))
    sorted_creators = sorted(all_creators)

    # Build module data
    for module in analysis.get("modules", []):
        mod = {
            "number": module.get("module_number", 0),
            "title": module.get("title", ""),
            "description": module.get("description", ""),
            "lessons": []
        }
        for lesson in module.get("lessons", []):
            mod["lessons"].append({
                "number": lesson.get("lesson_number", 0),
                "title": lesson.get("title", ""),
                "learning_outcome": lesson.get("learning_outcome", ""),
            })
        outline["modules"].append(mod)

    # Save outline JSON
    json_file = output_path / "outline.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)

    # Build Markdown
    md_lines = []
    md_lines.append(f"# {outline['course_title']}")
    md_lines.append(f"### {outline['course_subtitle']}")
    md_lines.append("")
    md_lines.append(f"**Target Audience:** {outline['target_audience']}")
    md_lines.append(f"**Modules:** {outline['total_modules']} | **Lessons:** {outline['total_lessons']}")
    md_lines.append("")

    if outline["pain_points"]:
        md_lines.append("## Problems This Course Solves")
        md_lines.append("")
        for pp in outline["pain_points"]:
            md_lines.append(f"- {pp}")
        md_lines.append("")

    md_lines.append("## Course Curriculum")
    md_lines.append("")

    for mod in outline["modules"]:
        md_lines.append(f"### Module {mod['number']}: {mod['title']}")
        md_lines.append(f"*{mod['description']}*")
        md_lines.append("")

        for lesson in mod["lessons"]:
            md_lines.append(f"  {mod['number']}.{lesson['number']} **{lesson['title']}**")
            md_lines.append(f"      → {lesson['learning_outcome']}")
            md_lines.append("")

    md_content = "\n".join(md_lines)

    # Save outline MD
    md_file = output_path / "outline.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Build sources reference (internal only — not exposed on site or course)
    ref_lines = []
    ref_lines.append(f"# Sources Reference — {outline['course_title']}")
    ref_lines.append("")
    ref_lines.append("**INTERNAL DOCUMENT — NOT FOR PUBLIC USE**")
    ref_lines.append("")
    ref_lines.append("This document tracks which creators and sources inspired each part of the course.")
    ref_lines.append("")

    if sorted_creators:
        ref_lines.append("## Source Creators")
        ref_lines.append("")
        for creator in sorted_creators:
            ref_lines.append(f"- {creator}")
        ref_lines.append("")

    ref_lines.append("## Module Attribution")
    ref_lines.append("")
    for module in analysis.get("modules", []):
        ref_lines.append(f"### Module {module.get('module_number', 0)}: {module.get('title', '')}")
        for lesson in module.get("lessons", []):
            creators = ", ".join(lesson.get("source_creators", []))
            ref_lines.append(f"- {lesson.get('title', '')}")
            if creators:
                ref_lines.append(f"  Sources: {creators}")
        ref_lines.append("")

    if analysis.get("frameworks"):
        ref_lines.append("## Frameworks Attribution")
        ref_lines.append("")
        for fw in analysis["frameworks"]:
            ref_lines.append(f"- **{fw.get('name', '')}** — {fw.get('creator', 'Unknown')}")
            ref_lines.append(f"  {fw.get('description', '')}")
        ref_lines.append("")

    ref_content = "\n".join(ref_lines)
    ref_file = output_path / "sources-reference.md"
    with open(ref_file, "w", encoding="utf-8") as f:
        f.write(ref_content)

    print(f"Outline saved:")
    print(f"  JSON: {json_file}")
    print(f"  MD:   {md_file}")
    print(f"  Sources: {ref_file}")
    print(f"\n{md_content}")

    return outline, md_content


def main():
    parser = argparse.ArgumentParser(description="Generate course outline from analysis")
    parser.add_argument("--analysis", "-a", required=True, help="Path to analysis.json")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    args = parser.parse_args()

    generate_outline(args.analysis, args.output)


if __name__ == "__main__":
    main()
