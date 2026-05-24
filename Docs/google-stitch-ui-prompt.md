# Google Stitch UI Prompt — Zomato AI (Next.js)

Use this document when generating **UI mockups, screens, or visual references** in [Google Stitch](https://stitch.withgoogle.com) for the restaurant recommendation frontend. The production implementation target is **Next.js** (App Router) calling an existing **FastAPI** backend on port `8001`.

---

## How to use in Stitch

1. Open Google Stitch and start a new design.
2. Set the framework / stack hint to **Next.js** (and React) if Stitch asks.
3. Paste the **Master prompt** below for a full-page layout, or use **Screen prompts** for individual frames.
4. Export screens as reference for building `Phase4-next/` or replacing the current static `Phase4/public` UI.

---

## Design system (keep consistent across screens)

| Token | Value |
|--------|--------|
| Primary brand | Zomato-style red `#E23744` |
| Background | Dark gradient `#0B0C10` → `#151B26` |
| Surface / cards | `#1A222D`, border `rgba(255,255,255,0.08)` |
| Text primary | `#F5F5F7` |
| Text muted | `#8B949E` |
| Font | **Outfit** (Google Font) — geometric, modern |
| Radius | 14px cards, 8px inputs |
| Accent glow | Soft red shadow on primary buttons |

**Mood:** Premium food-delivery app, dark mode, confident and appetizing — not playful cartoon.

---

## Master prompt (copy everything below)

```
Design a premium restaurant discovery web app called "Zomato AI" for Next.js (React, App Router, TypeScript, Tailwind CSS).

PRODUCT
AI-powered restaurant recommendations for Bangalore (India). Users set hard filters (location, cuisine, budget, rating, max cost for two in INR) plus natural-language "soft preferences" (e.g. quiet rooftop, family-friendly). The app shows top 5 AI-ranked restaurants with personalized explanation text per card. Multi-turn follow-up chat refines results using a session ID.

LAYOUT (desktop-first, responsive)
- Sticky header: logo "Zomato" with "AI" in red, small badge "Beta", right side: API status pill (green "API online" / red "API offline"), session ID chip, "New session" ghost button.
- Two-column main: LEFT sticky filter panel (~380px), RIGHT results area (fluid).
- Floating action button bottom-right opens a chat panel for follow-up questions.

LEFT PANEL — "Find restaurants"
- Location dropdown (Bangalore neighborhoods: Bellandur, Koramangala, Indiranagar, BTM, Whitefield, etc.)
- Cuisine text input
- Budget tier toggle group: $ / $$ / $$$
- Number input: "Max cost for two (₹)" placeholder 2000
- Minimum rating dropdown: Any, 3.5+, 4.0+, 4.5+
- Textarea: "Soft preferences" placeholder "Quiet rooftop, family-friendly, spicy food…"
- Full-width primary CTA button red gradient: "Get AI recommendations"

RIGHT PANEL — states
1) Welcome: dashed border card, plate emoji, headline "Discover your next meal", short subtitle about hybrid search and AI explanations.
2) Loading: three-step progress strip — "Filtering database…" → "AI reviewing matches…" → "Plating recommendations…" plus 3 shimmer skeleton cards in a responsive grid.
3) Results: agent summary bar (soft red tint) showing tools used; grid of restaurant cards (2 columns on desktop).
4) Empty / error states with friendly copy.

RESTAURANT CARD
- Top: gradient image placeholder band with rank badge "#1"
- Title + green rating pill "★ 4.4"
- Meta row: location pin, "₹1400 for two"
- Cuisine tags (max 3 visible + "+more")
- "AI Insight" panel: left red border, muted background, 2–3 lines of personalized explanation text

FLOATING CHAT
- Collapsed: circular red FAB with chat icon bottom-right
- Expanded: 380px panel above FAB, header "Follow-up chat", scrollable bubbles (user red right-aligned, assistant dark left), input + Send. Example user message: "Show me the first one with outdoor seating"

TECH / NEXT.JS NOTES (visual only, no backend code in mockup)
- Show realistic component boundaries suitable for Next.js Server/Client components
- Use Tailwind-style spacing and semantic HTML landmarks (header, main, aside)
- Accessible contrast, focus rings on inputs
- Mobile: stack filter panel above results; chat panel full-width sheet

Do not use stock photos of real restaurant brands. Use abstract food gradients or placeholder imagery only.
```

---

## Screen-specific prompts (optional)

### Screen 1 — Home / welcome

```
Next.js app screen: Zomato AI restaurant finder, dark premium theme, red accent #E23744, Outfit font. Split layout — left filter form (location, cuisine, budget $ $$ $$$, max cost ₹, rating, soft preferences textarea, red CTA), right welcome empty state "Discover your next meal" with subtle dashed card. Sticky header with logo and API online status. Desktop 1440px wireframe-quality UI mockup.
```

### Screen 2 — Loading

```
Next.js UI loading state for Zomato AI: dark background, horizontal 3-step progress (filtering, AI reviewing, plating), three shimmer skeleton restaurant cards in grid, left filter panel dimmed. Premium food app aesthetic, red accents.
```

### Screen 3 — Results grid

```
Next.js UI results view: 5 restaurant recommendation cards in 2-column grid, dark theme, red Zomato-style branding. Each card has image placeholder, rank badge, star rating, location, price for two in rupees, cuisine tags, "AI Insight" explanation box. Top agent status bar: "Found 15 candidates via hybrid_search". Header with session chip.
```

### Screen 4 — Chat follow-up

```
Next.js mobile-friendly chat overlay: floating panel bottom-right on restaurant results page, dark theme, red brand. Chat between user and assistant about refining restaurant picks. User bubble red, assistant bubble dark gray. Input field "Refine your picks…" and Send button. Restaurant cards visible blurred in background.
```

### Screen 5 — Mobile

```
Mobile responsive Zomato AI Next.js app, single column, dark mode, red CTA, filter form stacked, two restaurant result cards with AI insight sections, floating chat button. Premium Bangalore food discovery app.
```

---

## Next.js implementation checklist (after Stitch)

When translating Stitch output to code:

| Area | Approach |
|------|----------|
| Framework | Next.js 14+ App Router, TypeScript, Tailwind CSS |
| API base | `NEXT_PUBLIC_API_URL=http://127.0.0.1:8001` |
| Search | `POST /recommend` with filters + `description` |
| Session | Store `session_id` in `localStorage` or cookie; send on follow-up |
| Chat | Client Component; POST body `{ session_id, description }` only |
| Health | Poll `GET /health` for header status indicator |
| Components | `FilterPanel`, `RestaurantCard`, `ResultsGrid`, `ChatPanel`, `LoadingSkeleton` |

**API request shape (for developers):**

```json
{
  "session_id": "optional-uuid",
  "location": "Bellandur",
  "cuisine": "Italian",
  "budget_tier": "medium",
  "min_rating": 4.0,
  "max_cost": 2000,
  "description": "quiet rooftop with good views"
}
```

**Response shape:**

```json
{
  "session_id": "uuid",
  "recommendations": [
    {
      "name": "Restaurant Name",
      "rating": 4.4,
      "cost": 1400,
      "cuisines": "North Indian, Chinese",
      "location": "Bellandur",
      "explanation": "AI-generated rationale…"
    }
  ],
  "message": "Agent summary",
  "tools_used": ["hybrid_search", "format_recommendations"]
}
```

---

## Related docs

- [architecture.md](./architecture.md) — system layout and API contract  
- [../START_HERE.md](../START_HERE.md) — run backend + current static UI locally  
- [../Phase4/README.md](../Phase4/README.md) — existing HTML Phase 4 client  
