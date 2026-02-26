# Landing Page Structure — Guru

## Sales Page Framework

The LP template uses a proven info-product sales page structure. Each section has a specific job.

---

## Section Breakdown

### 1. Hero (above the fold)
**Job:** Stop the scroll. Create desire.
- Course title (big, bold)
- Subtitle (benefit-driven, 1 line)
- Hero image (16:9, full-width or contained)
- CTA button ("Start Learning →")
- Social proof snippet (optional: "Built from 500+ hours of expert content")

### 2. What You'll Master (module overview)
**Job:** Show the transformation. What will they be able to DO?
- 4-6 cards in a grid
- Each card: icon/emoji + module title + 1-sentence hook
- Visual: alternating colors or gradient backgrounds

### 3. Full Breakdown (curriculum accordion)
**Job:** Prove depth. Show they're getting their money's worth.
- Each module is an expandable accordion section
- Inside: numbered lessons with learning outcomes
- Total lessons count shown
- First module expanded by default

### 4. Built From the Best (creator attribution)
**Job:** Borrow credibility from known creators.
- "This course was built by analyzing content from the top creators in [niche]"
- Creator name cards/badges
- Optional: subscriber counts, channel focus areas

### 5. Pricing CTA (conversion section)
**Job:** Close the sale.
- Price: $97 one-time (no subscription)
- What's included checklist
- CTA button (large, contrasting color)
- Money-back guarantee badge
- "Instant access" messaging

### 6. FAQ (objection handling)
**Job:** Remove doubts.
- 4-5 questions formatted as accordions
- Common objections:
  - "Is this for beginners?"
  - "How is this different from free YouTube content?"
  - "How long do I have access?"
  - "What if it's not for me?"
  - "Do I need any special tools?"

### 7. Footer
**Job:** Legal + final CTA
- Mini CTA repeat
- Copyright
- Terms / Privacy links (placeholder)

---

## Copy Principles

1. **Benefits over features** — "Master meal prep in 30 minutes" not "6 modules on cooking"
2. **Specificity sells** — "47 lessons" not "comprehensive curriculum"
3. **Social proof through attribution** — "Built from 500+ hours of [Creator] content"
4. **Urgency without sleaze** — No fake countdown timers. Real value proposition.
5. **One CTA** — Every section flows to the same action: buy the course

---

## Design Principles

1. **Bold typography** — Large titles, clear hierarchy. Google Fonts, niche-appropriate
2. **CSS variables** — All colors defined as variables for easy niche-specific theming
3. **Mobile-first** — Grid → stack on mobile. Touch-friendly buttons.
4. **CSS-only animations** — Scroll-triggered fade-ins via `@keyframes` + `IntersectionObserver`
5. **No JS frameworks** — Vanilla HTML + CSS + minimal JS for accordions
6. **Fast** — No external deps except Google Fonts. Everything inline or local.

---

## Template Placeholders

All placeholders use `{{DOUBLE_BRACES}}` format:

| Placeholder | Description |
|-------------|-------------|
| `{{COURSE_TITLE}}` | Main course title |
| `{{COURSE_SUBTITLE}}` | Subtitle / tagline |
| `{{NICHE}}` | Niche name (lowercase) |
| `{{NICHE_CAPITALIZED}}` | Niche name (capitalized) |
| `{{TARGET_AUDIENCE}}` | Who the course is for |
| `{{TOTAL_MODULES}}` | Number of modules |
| `{{TOTAL_LESSONS}}` | Total lesson count |
| `{{HERO_IMAGE}}` | Path to hero image |
| `{{PRIMARY_COLOR}}` | CSS hex color |
| `{{SECONDARY_COLOR}}` | CSS hex color |
| `{{ACCENT_COLOR}}` | CSS hex color |
| `{{MODULE_CARDS}}` | HTML block of module cards |
| `{{CURRICULUM_ACCORDION}}` | HTML block of accordion sections |
| `{{FAQ_ITEMS}}` | HTML block of FAQ accordions |
| `{{PAIN_POINTS}}` | HTML block of pain point items |
| `{{FONT_FAMILY}}` | Google Font family name |
| `{{YEAR}}` | Current year |
