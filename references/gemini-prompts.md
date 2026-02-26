# Gemini Prompt Templates — Guru

## 1. Transcript Analysis Prompt

Used in `analyze_transcripts.py`. Sends merged transcripts to Gemini 2.0 Flash.

**Model:** `gemini-2.0-flash`
**Config:** `response_mime_type="application/json"`, `temperature=0.7`, `max_output_tokens=8192`

```
You are a world-class online course architect. You have been given transcripts from the top YouTube channels in the "{niche}" niche.

Your job:
1. Identify the CORE TOPICS these creators consistently teach
2. Extract the PAIN POINTS their audiences face
3. Identify proven FRAMEWORKS and METHODOLOGIES
4. Map the natural PROGRESSION PATH from beginner to advanced
5. Find GAPS — topics the audience needs but creators haven't covered well
6. Design a COMPLETE COURSE STRUCTURE with 4-6 modules, 3-5 lessons each

Rules:
- Course must be practical, not theoretical
- Each lesson must have a clear, actionable learning outcome
- Module order must follow a logical progression
- Include a compelling course title and subtitle that would sell
- Attribute which creator(s) inspired each module/lesson
```

**Response Schema:** JSON with `course_title`, `course_subtitle`, `target_audience`, `core_topics[]`, `pain_points[]`, `frameworks[]`, `gaps[]`, `modules[].lessons[]`

---

## 2. Hero Image Generation Prompt

Used in `generate_hero_image.py`. Generates a 16:9 hero image.

**Model:** `gemini-2.0-flash-preview-image-generation`
**Config:** `response_modalities=["IMAGE", "TEXT"]`

```
Create a premium, cinematic hero image for an online course about {niche}.

Style: {niche-specific style from NICHE_STYLES dict}

Requirements:
- 16:9 aspect ratio landscape orientation
- Rich, vibrant colors with professional color grading
- Depth of field with bokeh effect
- No text, no logos, no watermarks, no people's faces
- Premium stock photo quality — NOT generic, NOT AI-looking
- Warm, inviting, aspirational mood
- Course header quality for a $97 product page
```

**Niche Styles (presets):**
| Niche | Style |
|-------|-------|
| productivity | minimalist workspace, morning light, clean lines |
| cooking | artisanal kitchen, warm tones, fresh ingredients |
| personal finance | elegant planning scene, growth charts |
| fitness | dynamic athletic training, energy, modern gym |
| marketing | creative workspace, dashboards, growth |
| photography | camera gear, landscape backdrop, golden hour |
| meditation | serene zen space, soft natural light, peaceful |
| programming | futuristic coding env, multiple monitors |
| design | creative studio, color palettes, artistic |
| business | executive environment, city skyline, success |

---

## 3. v0 Landing Page Generation Prompt

Used in `generate_landing_page.py`. Generates a full standalone HTML landing page via v0 API.

**API:** `POST https://api.v0.dev/v1/chat/completions` (OpenAI-compatible)
**Model:** `v0-1.5-md` (128K input, 64K output)
**Auth:** Bearer token via `V0_API_KEY` env var
**Config:** `max_completion_tokens=16000` (retry with 32000), `stream=false`

**System prompt** — prescriptive design constraints:
```
You are a world-class landing page designer. Generate a SINGLE, COMPLETE, STANDALONE HTML file.

CRITICAL RULES:
- Output ONLY a single HTML file with ALL CSS inline in a <style> tag
- NO React, NO JSX, NO components, NO imports, NO build steps
- NO external dependencies except ONE Google Fonts link
- Dark theme ONLY (background: #0a0a0a)
- Mobile-first responsive design
- Use CSS custom properties for colors
- Include IntersectionObserver for scroll reveal animations
- Include accordion JS for curriculum and FAQ sections

COLOR SCHEME: Uses niche-specific colors from NICHE_COLORS dict
FONT: Niche-specific Google Font

REQUIRED SECTIONS (exact order):
1. HERO — Full viewport, gradient title, stats bar, CTA → #pricing
2. PAIN POINTS — Emoji card grid from sales copy
3. MODULES — Card grid with number, icon, title, hook, lesson count
4. CURRICULUM ACCORDION — Expandable per-module, first open by default
5. PRICING — $97, feature checklist, guarantee badge
6. FAQ — Accordion, objection handling
7. FOOTER — Final CTA + copyright
```

**User message** contains JSON with: course title, subtitle, niche, total modules/lessons/videos, pain points array, modules array with lessons, and optionally truncated sales copy (first 6000 chars).

**HTML Extraction Logic:**
1. Try markdown code fence: ` ```html ... ``` `
2. Try raw `<!DOCTYPE html>...</html>`
3. Content starts with `<!doctype`
4. Else: extraction failed → fallback to template

**Validation Checks:**
- Starts with `<!DOCTYPE html>`, ends with `</html>`
- Contains `<style>` tag
- Contains `id="pricing"`
- Has 3+ `<section` tags
- Size between 5KB and 200KB
- Course title text is present
- No React/JSX indicators

**Error Handling:**
| Scenario | Action |
|----------|--------|
| V0_API_KEY not set | Skip v0, use template fallback |
| API timeout (120s) | Retry once with 32K tokens, then fallback |
| HTTP 429 (rate limit) | Fallback immediately |
| Truncated HTML | Retry with max_tokens=32000 |
| React/JSX output | Fallback immediately (v0 tends to repeat) |
| sales-copy.md missing | Use outline data + generic copy |

---

## 4. Landing Page Copy Enhancement (optional, in SKILL.md)

Used inline by Claude when customizing the LP template. Not a separate script.

```
Given this course outline, write compelling sales copy for each section:
- Hero: 1 headline (max 8 words), 1 subtitle (max 20 words)
- Module cards: 1 icon emoji + 1 hook sentence per module
- FAQ: 5 questions a skeptical buyer would ask, with reassuring answers
- CTA: 2 variations of a call-to-action button text

Tone: Direct, confident, zero fluff. Like a course from someone who's actually done it.
Niche: {niche}
Course: {course_title}
```
