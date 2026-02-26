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

## 3. Landing Page Copy Enhancement (optional, in SKILL.md)

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
