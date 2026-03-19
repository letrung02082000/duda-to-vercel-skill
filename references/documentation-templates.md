# Documentation Templates

Generate these 3 files during migration. Replace all `{{PLACEHOLDER}}` values with project-specific data.

---

## Placeholders Reference

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{PROJECT_NAME}}` | Client/site name | Tigers Towing & Transport |
| `{{DOMAIN}}` | Production domain | www.tigerstowingtransport.com |
| `{{STAGING_URL}}` | Vercel preview URL | tigers-towing-transport.vercel.app |
| `{{DUDA_SITE_ID}}` | Duda export folder or URL | f3e657b8 |
| `{{REPO_URL}}` | GitHub repo URL | https://github.com/org/repo |
| `{{SKILL_REPO_URL}}` | Migration skill repo | https://github.com/letrung02082000/duda-to-vercel-skill |
| `{{PAGE_COUNT}}` | Total pages discovered | 9 |
| `{{DEVICE_COUNT}}` | Always 3 | 3 |
| `{{HTML_FILE_COUNT}}` | PAGE_COUNT × 3 | 27 |
| `{{ROUTE_TABLE}}` | Built from Step 1 route map | See template |
| `{{PAGE_TABLE}}` | Route map + sitemap status | See template |
| `{{SITEMAP_COUNT}}` | URLs in sitemap.xml | 6 |
| `{{FONT_NAME}}` | From CSS @font-face | Inter |
| `{{FONT_WEIGHTS}}` | From CSS @font-face | 100-900 |
| `{{SLIDER_INFO}}` | From homepage HTML analysis | 2 sliders: 4 slides + 6 slides |
| `{{DATE}}` | Migration date | MM/DD/YYYY |

---

## Template 1: README.md

```markdown
# {{PROJECT_NAME}} — Duda to Vercel Migration

A Duda MultiScreen website migrated to a Next.js static site deployed on Vercel, with Edge Middleware for server-side device detection.

## Migration Overview

| Item | Detail |
|------|--------|
| **Source** | Duda MultiScreen export (site ID `{{DUDA_SITE_ID}}`) |
| **Target** | Vercel (Next.js 15 + Edge Middleware) |
| **AI Model** | Claude Opus 4.6 (via GitHub Copilot) |
| **Pages** | {{PAGE_COUNT}} pages × {{DEVICE_COUNT}} devices = {{HTML_FILE_COUNT}} HTML files |
| **Devices** | Desktop, Mobile, Tablet |

## Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/) (React 19)
- **Runtime**: Edge Middleware (server-side device detection via User-Agent)
- **Language**: TypeScript
- **Deployment**: [Vercel](https://vercel.com/)
- **Styling**: Original Duda CSS (desktop.css, mobile.css, tablet.css) + per-page inline styles
- **JavaScript**: Original Duda webpack runtime + custom `duda-stubs.js` for platform compatibility

## Architecture

\```
Request → Edge Middleware → Device Detection → Rewrite to /_pages/{device}/{page}/index.html
\```

The Duda export produces separate HTML/CSS/JS for each device breakpoint. Edge Middleware detects the visitor's device from the `User-Agent` header and rewrites the request to the correct HTML file — all at the edge, before hitting the origin.

### Project Structure

\```
├── app/                    # Next.js app directory (minimal — just enables the framework)
├── middleware.ts            # Edge Middleware: device detection + URL rewriting
├── vercel.json              # Redirects (/home → /) + cache headers for static assets
├── public/
│   ├── _pages/
│   │   ├── desktop/         # Desktop HTML pages
│   │   ├── mobile/          # Mobile HTML pages
│   │   └── tablet/          # Tablet HTML pages
│   ├── Scripts/
│   │   ├── runtime.js       # Duda webpack runtime (publicPath patched)
│   │   ├── desktop.js       # Desktop device JS
│   │   ├── mobile.js        # Mobile device JS
│   │   ├── tablet.js        # Tablet device JS
│   │   ├── duda-stubs.js    # Custom stubs for missing Duda platform deps
│   │   └── *.js             # Webpack chunks (animations, widgets, etc.)
│   ├── Style/               # Device-specific CSS
│   └── Resources/           # Images, files
├── Pages/                   # Original Duda export (kept for reference)
├── Scripts/                 # Original Duda export scripts
├── Style/                   # Original Duda export styles
└── Resources/               # Original Duda export resources
\```

### Pages

{{ROUTE_TABLE}}
<!-- Format:
| Route | Folder |
|-------|--------|
| `/` | `home` |
| `/about-us` | `about-us` |
-->

## Migration Process

### 1. Export from Duda
Export the MultiScreen site from Duda. The export contains separate `desktop/`, `mobile/`, `tablet/` folders under `Pages/`, plus shared `Scripts/`, `Style/`, and `Resources/` directories.

### 2. Restructure for Next.js
Move the Duda export into `public/` with renamed paths:
- `Pages/` → `public/_pages/` (prefix with underscore to avoid Next.js routing conflicts)
- `Scripts/`, `Style/`, `Resources/` → `public/Scripts/`, `public/Style/`, `public/Resources/`

### 3. Fix HTML files
Automated via [`fix_html.py`]({{SKILL_REPO_URL}}/blob/main/scripts/fix_html.py):
- Convert relative navigation links to absolute paths
- Update CSS `<link>` paths from `/Pages/` to `/_pages/`
- Update canonical/OG URLs to the new domain
- Inject `duda-stubs.js` script tag between device JS and `runtime.js`

### 4. Fix runtime.js publicPath
Duda's webpack runtime (`runtime.js`) has a hardcoded `publicPath` pointing to Duda's editor CDN. Patch `a.p="..."` to `a.p="/Scripts/"` so webpack chunks load from the local server.

### 5. Create duda-stubs.js
A custom JavaScript file that provides missing Duda platform dependencies:
- `window.flexSite = true` — enables hamburger navigation
- jQuery/`$` stub with `$.DM` namespace — prevents runtime errors
- `window.rtCommonProps` / `window.commonProps` — webpack chunk config stubs
- SSR Accordion hydration — replaces the never-resolved `waitForDeferred('ssrLibrariesLoaded')`
- SSR Image Slider hydration — injects missing `<img>` tags and drives auto-pagination
- `window.runtime.initWidgets()` trigger — kicks off animation and widget initialization

### 6. Create Edge Middleware
`middleware.ts` maps clean URLs to device-specific HTML files using User-Agent detection.

### 7. Configure Vercel
`vercel.json` handles:
- Redirect `/home` → `/` (Duda's home page convention)
- Cache headers for static assets (1 year, immutable)

## Known Issues & Solutions

<!-- Fill in issues encountered during this specific migration -->
| Issue | Root Cause | Solution |
|-------|-----------|----------|
| **Animations don't play** | `runtime.js` publicPath points to Duda CDN → webpack chunks 404 | Patch `a.p=` in `runtime.js` to `/Scripts/` |
| **Hamburger opens then immediately closes** | Double-toggle bug: two click handlers | Set `window.flexSite = true` only. Do NOT add `.layout-drawer-hamburger` class. |
| **FAQ accordion not clickable** | SSR hydration never fires in static export | Lightweight click handler stub in `duda-stubs.js` |
| **Image slider shows only first 2 images** | Duda SSR only renders `<img>` for visible slots | `initSliders()` in duda-stubs.js injects missing `<img>` elements |

## Script Load Order

The device JS, stubs, and runtime must load in this exact order in every HTML file:

\```html
<script src="/Scripts/{device}.js"></script>
<script src="/Scripts/duda-stubs.js"></script>
<script src="/Scripts/runtime.js"></script>
\```

## Development

\```bash
npm install
npm run dev       # Start dev server at http://localhost:3000
npm run build     # Build for production
npx playwright test   # Run tests
\```

## Deployment

Push to the connected Git repository. Vercel auto-deploys on push to `main`.

## Reusable Skill

The migration process is packaged as a reusable Claude Copilot skill:

**Repository:** {{SKILL_REPO_URL}}

This skill automates the Duda → Vercel migration, including HTML path fixing, `duda-stubs.js` generation, and Edge Middleware setup. See the repo's `SKILL.md` for the full guide.
```

---

## Template 2: GUIDE-SEO-DESIGN.md

```markdown
# Website Update Guide — For SEO & Design Teams

> **Project:** {{PROJECT_NAME}}
> **Domain:** `{{DOMAIN}}`
> **Platform:** Duda → Vercel (Next.js + Edge Middleware)
> **Last updated:** {{DATE}}

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Page List](#2-page-list)
3. [Guide for SEO Team](#3-guide-for-seo-team)
4. [Guide for Design Team](#4-guide-for-design-team)
5. [Change Request Workflow](#5-change-request-workflow)
6. [Important Notes](#6-important-notes)

---

## 1. Architecture Overview

The website is **static HTML** exported from Duda and deployed on Vercel. Each page has **3 separate versions** for each device type:

| Device | Directory | When Served |
|--------|-----------|-------------|
| Desktop | `public/_pages/desktop/` | Screen ≥ 1025px, bots/crawlers |
| Tablet | `public/_pages/tablet/` | iPad, Android tablets |
| Mobile | `public/_pages/mobile/` | iPhone, Android phones |

**Important:** When requesting content or layout changes, you must specify which **device(s)** the change applies to (or all).

### File Structure

\```
public/
├── _pages/
│   ├── desktop/{page-name}/index.html    ← Desktop HTML
│   ├── mobile/{page-name}/index.html     ← Mobile HTML
│   └── tablet/{page-name}/index.html     ← Tablet HTML
├── Resources/images/                      ← All images
├── Scripts/                               ← JavaScript
└── Style/
    ├── desktop.css                        ← Desktop-specific CSS
    ├── mobile.css                         ← Mobile-specific CSS
    └── tablet.css                         ← Tablet-specific CSS
\```

---

## 2. Page List

{{PAGE_TABLE}}
<!-- Format:
| # | URL | Directory | In Sitemap |
|---|-----|-----------|:---:|
| 1 | `/` (Homepage) | `home/` | ✅ |
| 2 | `/about-us` | `about-us/` | ✅ |
| 3 | `/thank-you` | `thank-you/` | ❌ |
-->

---

## 3. Guide for SEO Team

### 3.1. Meta Tags — Current Status

Each HTML page has the following meta tags (inside `<head>`):

| Meta Tag | Example (Homepage) | File to Edit |
|----------|-------------------|--------------|
| `<title>` | <!-- Fill from actual homepage --> | `index.html` per device |
| `<meta name="description">` | <!-- Fill from actual homepage --> | `index.html` per device |
| `<meta name="keywords">` | <!-- Fill from actual homepage --> | `index.html` per device |
| `<link rel="canonical">` | `https://{{DOMAIN}}/` | `index.html` per device |
| `<meta property="og:title">` | Same as title | `index.html` per device |
| `<meta property="og:description">` | Same as description | `index.html` per device |
| `<meta property="og:image">` | <!-- Fill from actual homepage --> | `index.html` per device |
| `<meta name="twitter:card">` | `summary` | `index.html` per device |

### 3.2. Meta Tag Change Requests

\```
📋 SEO REQUEST - META TAGS
───────────────────────────
Page:         [URL or page name]
Device:       [Desktop / Mobile / Tablet / All]
Changes:
  - Title:       [new content]
  - Description: [new content]
  - Keywords:    [new content]
  - OG Image:    [new image URL if applicable]
  - Canonical:   [new URL if needed]
Notes:        [...]
\```

> ⚠️ **Note:** All **3 versions** (desktop, mobile, tablet) must be updated for each page.

### 3.3. Sitemap

- **File:** `sitemap.xml` (root)
- **Current:** {{SITEMAP_COUNT}} URLs
- **Referenced in:** `public/robots.txt`

\```
📋 SEO REQUEST - SITEMAP
─────────────────────────
Action:       [Add / Remove / Update]
URL:          [full URL path]
Priority:     [0.0 - 1.0, default 1.0]
Changefreq:   [daily / weekly / monthly]
Notes:        [...]
\```

### 3.4. Robots.txt

- **File:** `public/robots.txt`
- **Current:** Allows crawling everything, blocks `/_pages/` and `/Scripts/`
- **Sitemap URL:** `https://{{STAGING_URL}}/sitemap.xml`

> ⚠️ Update sitemap URL to the official domain before go-live.

### 3.5. Structured Data (JSON-LD)

**Current status:** ❌ No JSON-LD structured data implemented.

**Recommended additions:**
- `LocalBusiness` — business info, hours, address
- `Service` — services offered
- `BreadcrumbList` — for nested sub-pages
- `FAQPage` — if there is FAQ content

\```
📋 SEO REQUEST - STRUCTURED DATA
──────────────────────────────────
Page:         [URL]
Schema type:  [LocalBusiness / Service / FAQ / ...]
Data:
  - Name:      {{PROJECT_NAME}}
  - Phone:     [phone number]
  - Address:   [...]
  - Hours:     [...]
\```

### 3.6. Favicon

**Current status:** ❌ Not configured.

Provide: `favicon.ico` (32×32), `apple-touch-icon.png` (180×180), OG image (1200×630).

### 3.7. Google Analytics / Tracking

**Current status:** Not installed.

\```
📋 SEO REQUEST - TRACKING
──────────────────────────
Type:         [GA4 / GTM / Facebook Pixel / ...]
ID:           [G-XXXXXXXXXX or GTM-XXXXXXX]
Scope:        [All pages / Specific pages]
\```

### 3.8. Adding New Pages

\```
📋 SEO REQUEST - NEW PAGE
──────────────────────────
Desired URL:    [e.g., /services/new-service]
Title:          [...]
Description:    [...]
Add to sitemap: [Yes / No]
Template:       [Clone from which page, or new design]
Content:        [Attach content file]
\```

> ⚠️ Adding a new page requires creating HTML for all 3 devices and updating the route in `middleware.ts`.

---

## 4. Guide for Design Team

### 4.1. Design Tool — Use Figma

**Figma** is the recommended design tool. It provides the best designer-to-developer handoff:

| Reason | Detail |
|--------|--------|
| **Dev Mode** | Developers inspect CSS values directly from the design |
| **Export assets** | Export as PNG, JPG, SVG, or WebP at any resolution |
| **Responsive frames** | Design for all 3 breakpoints side by side |
| **Share via link** | Just share the Figma link |
| **Version history** | All iterations tracked automatically |

#### Figma Setup

Create **3 frames** per page:

| Frame Name | Width | Maps To |
|------------|-------|---------|
| `{Page} / Desktop` | 1440px | `public/_pages/desktop/{page}/` |
| `{Page} / Tablet` | 768px | `public/_pages/tablet/{page}/` |
| `{Page} / Mobile` | 375px | `public/_pages/mobile/{page}/` |

### 4.2. Design Handoff Workflow

\```
Designer creates/updates in Figma
        ↓
Share Figma link with developer
        ↓
Developer inspects via Figma Dev Mode
        ↓
Developer extracts CSS values + exports assets
        ↓
Developer updates HTML/CSS files
\```

#### What to Provide

| Item | Format |
|------|--------|
| Layout changes | Figma link (Dev Mode enabled) |
| Color values | HEX or RGB (from Figma) |
| Spacing/sizing | px values (from Figma) |
| Icons | **SVG** (vector) |
| Photos/images | **JPG** 80-85% quality or **PNG** for transparency |
| New section | Figma frame for all 3 breakpoints |

#### What NOT to Do

- ❌ Do not export HTML/CSS from Figma — project uses Duda's original HTML
- ❌ Do not use fonts other than **{{FONT_NAME}}** without developer approval
- ❌ Do not design at arbitrary widths — use 1440px, 768px, 375px
- ❌ Do not send PSD/AI files — use Figma

### 4.3. Technical Specifications

| Specification | Value |
|---------------|-------|
| **Primary font** | {{FONT_NAME}} (variable, {{FONT_WEIGHTS}}) |
| **Font hosting** | Self-hosted (WOFF2) in `/Resources/files/` |
| **Desktop breakpoint** | ≥ 1025px |
| **Tablet breakpoint** | 768px - 1024px |
| **Mobile breakpoint** | ≤ 767px |

### 4.4. Image Specifications

| Type | Recommended Size | Format |
|------|-----------------|--------|
| Hero/Slider | 1920×auto (desktop), 640×auto (mobile) | JPG |
| Card/Thumbnail | 640×auto | JPG |
| Logo | 1920w, 640w, 80w | PNG |
| Icon | SVG | SVG |
| OG Image | 1200×630 | JPG |

### 4.5. Design Change Request Template

\```
📋 DESIGN REQUEST
──────────────────
Figma Link:      [paste Figma frame URL]
Page:            [URL or page name]
Device:          [Desktop / Mobile / Tablet / All]
Type:            [Layout / Color / Image / Typography / New Section]
Description:     [brief summary]
Assets attached: [list exported images/icons]
Notes:           [...]
\```

### 4.6. Image Slider

<!-- Fill from actual homepage analysis -->
{{SLIDER_INFO}}

\```
📋 DESIGN REQUEST - SLIDER
────────────────────────────
Figma Link:       [if new slide designed in Figma]
Page:             [URL]
Slider:           [Slider 1 / Slider 2 / ...]
Action:           [Add slide / Remove slide / Replace image / Reorder]
Image:            [attached file + alt text]
Rotation speed:   [seconds, default 2s]
\```

> ⚠️ Slider changes require updating both the HTML structure and the hydration config. A developer must handle this.

---

## 5. Change Request Workflow

### Step 1: Create the Request
Use the templates above. Attach: screenshot, source images, new text, mockup/wireframe.

### Step 2: Send to Developer
Send via Slack/Jira with: `[SEO]` or `[DESIGN]` prefix + completed template + attachments.

### Step 3: Developer Implements
Developer will: update across all devices → test locally → commit & push → Vercel auto-deploys.

### Step 4: Review
Check on Vercel preview URL. Verify Desktop, Mobile, Tablet. Use Chrome DevTools for responsive testing.

---

## 6. Important Notes

### ⚠️ Static Website Characteristics

| What to Know | Details |
|-------------|---------|
| **3 separate versions** | Every change must be updated on desktop, mobile AND tablet |
| **No CMS** | All changes require a developer |
| **No dynamic content** | Forms, blogs etc. must be handled externally |
| **1-year cache for assets** | Rename files when updating images/CSS/JS |
| **Bots get Desktop** | Optimize SEO for the desktop version |

### ⚠️ Pre-Request Checklist

- [ ] Specify **which page** (URL or name)
- [ ] Specify **which device(s)** (Desktop / Mobile / Tablet / All)
- [ ] Specify **location on the page** (screenshot if possible)
- [ ] Provide **exact content** (text, images, links)
- [ ] Provide **alt text** for all images
- [ ] Check **spelling** before submitting

### ⚠️ Things You Should NOT Do

- ❌ Do not edit HTML/CSS/JS files yourself
- ❌ Do not commit directly to Git
- ❌ Do not upload files directly to Vercel
- ❌ Do not change the directory structure
```

---

## Template 3: GUIDE-DEVELOPER.md

```markdown
# Developer Workflow Guide — {{PROJECT_NAME}}

> **Project:** {{PROJECT_NAME}}
> **Stack:** Next.js 15 + React 19 + Edge Middleware on Vercel
> **Repo:** {{REPO_URL}}
> **Last updated:** {{DATE}}

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [AI-Assisted Development Setup](#2-ai-assisted-development-setup)
3. [Branching Strategy](#3-branching-strategy)
4. [Receiving & Processing Change Requests](#4-receiving--processing-change-requests)
5. [Development Workflow](#5-development-workflow)
6. [Writing Tests with Playwright](#6-writing-tests-with-playwright)
7. [Testing Workflow — Integrated Browser](#7-testing-workflow--integrated-browser)
8. [Pull Request Process](#8-pull-request-process)
9. [Deployment](#9-deployment)
10. [Project Architecture Reference](#10-project-architecture-reference)

---

## 1. Getting Started

### Prerequisites

- Node.js ≥ 18
- npm ≥ 9
- Git

### Initial Setup

\```bash
git clone {{REPO_URL}}
cd <project-directory>
npm install
npx playwright install --with-deps
\```

### npm Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| `dev` | `next dev` | Local development server |
| `build` | `next build` | Production build |
| `start` | `next start` | Serve production build |
| `test` | `npx playwright test` | Run all Playwright tests |
| `test:ui` | `npx playwright test --ui` | Open Playwright UI mode |
| `test:headed` | `npx playwright test --headed` | Run tests in visible browser |
| `test:report` | `npx playwright show-report` | View HTML test report |

---

## 2. AI-Assisted Development Setup

This project relies on **Claude Opus 4.6** as the primary AI coding assistant.

### Option A: VS Code + GitHub Copilot (Recommended)

1. Install **GitHub Copilot** + **GitHub Copilot Chat** extensions
2. Open Copilot Chat → click model selector → select **Claude Opus 4.6**
3. Use **Agent mode** for multi-file changes (e.g., updating all 3 device versions)

| Feature | Shortcut | Use For |
|---------|----------|--------|
| Inline Chat | `Ctrl+I` | Quick edits in current file |
| Chat Panel | `Ctrl+Shift+I` | Questions, explanations |
| Agent Mode | Chat → Agent | Multi-file edits, complex tasks |

> ⚠️ Claude Opus 4.6 is required — the migration skill and prompts are optimized for Claude.

### Option B: Claude Code (Terminal-Based)

\```bash
npm install -g @anthropic-ai/claude-code
cd <project-directory>
claude
\```

### Best Practices

| Practice | Detail |
|----------|--------|
| **Always specify devices** | Tell the AI "all 3 devices" or "desktop only" |
| **Review before accepting** | Check all 3 HTML files were updated |
| **Run tests after AI edits** | `npx playwright test` |
| **Use the migration skill** | For new migrations: [duda-to-vercel skill]({{SKILL_REPO_URL}}) |

---

## 3. Branching Strategy

### Branch Naming

\```
{type}/{short-description}
\```

| Type | When to Use | Example |
|------|-------------|---------|
| `feat/` | New page, section, feature | `feat/new-landing-page` |
| `fix/` | Bug fixes | `fix/slider-image-missing` |
| `seo/` | SEO changes | `seo/homepage-meta-tags` |
| `design/` | Visual/UI changes | `design/hero-redesign` |
| `content/` | Text updates only | `content/about-us-copy` |
| `chore/` | Config, tooling, docs | `chore/add-tests` |

### Rules

- **Never push directly to `main`** — it auto-deploys to production
- **Always create a feature branch** from `main`
- **One change per branch**
- **Delete branch after merge**

### Commit Messages

\```
{type}: {short description}

Examples:
  feat: add new landing page
  fix: inject missing slider images
  seo: update homepage meta tags
  design: change hero background color
\```

---

## 4. Receiving & Processing Change Requests

Requests come from SEO/Design teams using templates in [GUIDE-SEO-DESIGN.md](GUIDE-SEO-DESIGN.md).

### Finding the Right Files

| Change Type | Files to Edit |
|-------------|---------------|
| Meta tags | `public/_pages/{device}/{page}/index.html` — `<head>` |
| Text content | `public/_pages/{device}/{page}/index.html` — `<body>` |
| Images | `public/Resources/images/` + HTML `src` |
| Colors, spacing | `public/Style/{device}.css` |
| Slider images | HTML + hydration config in `<script>` tag |
| Sitemap | `sitemap.xml` (root) |
| New page | HTML for 3 devices + route in `middleware.ts` |

### Multi-Device Checklist

- [ ] Desktop updated
- [ ] Mobile updated
- [ ] Tablet updated
- [ ] Tested all 3 versions

---

## 5. Development Workflow

\```bash
npm run dev    # http://localhost:3000
\```

Test devices via User-Agent override in Chrome DevTools, or access directly:
- `http://localhost:3000/_pages/desktop/{page}/index.html`
- `http://localhost:3000/_pages/mobile/{page}/index.html`
- `http://localhost:3000/_pages/tablet/{page}/index.html`

---

## 6. Writing Tests with Playwright

Playwright config (`playwright.config.ts`) runs tests across 3 device projects:
- **desktop** — Desktop Chrome with standard User-Agent
- **mobile** — iPhone 14
- **tablet** — iPad (gen 7)

### Test Structure

\```
tests/
├── pages/           ← Page-specific tests
├── seo/             ← Meta tags, sitemap validation
├── components/      ← Navigation, slider, FAQ tests
└── visual/          ← Visual regression (optional)
\```

---

## 7. Testing Workflow — Integrated Browser

\```bash
npx playwright test                    # Run all tests
npx playwright test --project=desktop  # Desktop only
npx playwright test --ui               # Interactive UI mode
npx playwright test --headed           # Visible browser
npx playwright show-report             # View report
\```

### Testing Checklist (Before Every PR)

- [ ] All 3 device projects pass
- [ ] Content-sync tests pass (if content changed)
- [ ] SEO tests pass (if meta tags changed)
- [ ] Component tests pass (if UI changed)

---

## 8. Pull Request Process

1. Push branch → GitHub → New Pull Request (base: `main`)
2. Fill in PR template (pages affected, devices updated, change type)
3. Vercel creates preview deployment automatically
4. Review on preview URL across all 3 devices
5. **Squash and merge** → auto-deploys to production
6. Delete branch

### PR Rules

- Never merge your own PR
- All tests must pass
- Preview URL must be verified
- Squash and merge to keep clean history

---

## 9. Deployment

| Trigger | Result |
|---------|--------|
| Push to `main` | Auto-deploys to **production** |
| Push to other branch | Creates **preview deployment** |

### Rollback

\```bash
git revert <merge-commit-hash>
git push origin main
\```

Or: Vercel Dashboard → Deployments → Promote previous deployment.

---

## 10. Project Architecture Reference

### Key Files

| File | Purpose |
|------|---------|
| `middleware.ts` | Edge Middleware — device detection + route mapping |
| `next.config.js` | Next.js config |
| `vercel.json` | Redirects + cache headers |
| `sitemap.xml` | XML sitemap |
| `public/robots.txt` | Crawler rules |
| `public/Scripts/duda-stubs.js` | Duda compatibility layer |
| `public/Scripts/runtime.js` | Webpack runtime |
| `playwright.config.ts` | Test configuration |

### Route Map

{{ROUTE_TABLE}}
<!-- Format:
| URL Path | → `_pages/{device}/` Folder |
|----------|------------------------------|
| `/` | `home/` |
| `/about-us` | `about-us/` |
-->

### Device Detection

\```
User-Agent → detectDevice()
  ├── /iphone|ipod|blackberry|windows phone/ → mobile
  ├── /android/ + /mobile/                   → mobile
  ├── /ipad|tablet|silk/                     → tablet
  ├── /android/ + NOT /mobile/               → tablet
  └── everything else (+ bots/crawlers)      → desktop
\```
```

---

## How to Use These Templates

During migration Step 10, for each template:

1. Copy the template content above
2. Search and replace all `{{PLACEHOLDER}}` values with project-specific data
3. Fill in tables (route map, page list) from the data gathered in Step 1
4. Fill in meta tag examples by reading the actual homepage `<head>` tags
5. Fill in slider info by analyzing the homepage HTML
6. Fill in font info from the CSS `@font-face` declarations
7. Add any project-specific known issues to the README
8. Commit all 3 files to the repo root
