---
name: duda-to-vercel
description: Convert Duda MultiScreen website exports into Vercel-deployable Next.js projects with Edge Middleware for server-side device detection. Use when converting a Duda.co static HTML export (with separate desktop/mobile/tablet folders) into a production-ready static site on Vercel. Triggers on tasks involving Duda exports, MultiScreen site conversion, device-specific HTML serving, or migrating page-builder sites to Vercel. Also use when the workspace contains a Pages/ directory with desktop/mobile/tablet subdirectories, Scripts/ with runtime.js and device-specific JS files (desktop.js, mobile.js, tablet.js), Style/ with device CSS files, and Resources/ with images and fonts — all hallmarks of a Duda export.
---

# Duda to Vercel Conversion

Convert Duda MultiScreen website exports into Next.js projects deployable on Vercel, preserving pixel-perfect responsive layouts across desktop, tablet, and mobile.

## Duda Export Anatomy

A Duda export always has this structure:

```
project-root/
├── Pages/
│   ├── desktop/       # Full HTML pages for desktop
│   │   ├── home/index.html + style.css
│   │   ├── about-us/index.html + style.css
│   │   └── ...
│   ├── mobile/        # Identical structure, mobile-optimized
│   └── tablet/        # Identical structure, tablet-optimized
├── Scripts/
│   ├── runtime.js     # Duda's webpack runtime (~500KB minified)
│   ├── desktop.js     # Device config: window._currentDevice = 'desktop'
│   ├── mobile.js      # Device config: window._currentDevice = 'mobile'
│   ├── tablet.js      # Device config: window._currentDevice = 'tablet'
│   └── *.js           # Lazy-loaded widget/feature chunks
├── Style/
│   ├── desktop.css    # Global desktop styles
│   ├── mobile.css     # Global mobile styles
│   └── tablet.css     # Global tablet styles
├── Resources/
│   ├── images/        # Responsive image variants ({name}-{width}w.{ext})
│   └── files/         # Fonts (woff2, woff, ttf) and other assets
└── sitemap.xml        # URL list for the site
```

Key characteristics:
- **No root index.html** — Duda's server handles device routing
- **3 complete HTML sets** — not media-query responsive, but separate builds per device
- **Relative navigation links** (`../contact-us/`, `../../../home/`)
- **Absolute asset paths** (`/Resources/images/...`, `/Style/desktop.css`)
- **Page-specific CSS** in each page folder (`Pages/desktop/home/style.css`)
- **CSS paths reference** `/Pages/desktop/...` (must be updated to `/_pages/desktop/...`)
- **device JS files** contain `window.Parameters`, Schema.org structured data, analytics

## Conversion Workflow

### Step 1: Discover pages and routes

1. Parse `sitemap.xml` to get all public URLs
2. List `Pages/desktop/` subdirectories to find all pages (including noindex pages like thank-you, privacy-policy, terms-conditions not in sitemap)
3. Build a route map: clean URL path -> page folder name

Example route map:
```
/                                    -> home
/about-us                            -> about-us
/contact-us                          -> contact-us
/texas/cypress/towing-services       -> texas/cypress/towing-services
/thank-you                           -> thank-you        (noindex)
/privacy-policy                      -> privacy-policy   (noindex)
/terms-conditions                    -> terms-conditions  (noindex)
```

### Step 2: Create Next.js project

Create minimal Next.js project files. See [references/nextjs-files.md](references/nextjs-files.md) for exact file contents.

Required files:
- `package.json` — dependencies: next, react, react-dom
- `next.config.js` — minimal config
- `tsconfig.json` — TypeScript config
- `app/layout.tsx` — root layout (minimal, just passes children)
- `app/page.tsx` — empty placeholder (middleware handles all routing)

### Step 3: Restructure into public/

Run `scripts/restructure.py` to copy assets into Next.js `public/` directory:

```bash
python scripts/restructure.py <duda-export-dir> <nextjs-project-dir>
```

This copies:
- `Resources/` -> `public/Resources/`
- `Scripts/` -> `public/Scripts/`
- `Style/` -> `public/Style/`
- `Pages/` -> `public/_pages/` (renamed to avoid Next.js App Router conflict)

### Step 4: Fix HTML files

Run `scripts/fix_html.py` to fix all HTML files in `public/_pages/`:

```bash
python scripts/fix_html.py <nextjs-project-dir>/public/_pages <route-map-json>
```

This script performs:

1. **Fix navigation links** — convert relative paths to absolute:
   - Compute each page's depth to determine how many `../` to strip
   - `../home/` and `./` from home page -> `/`
   - `../contact-us/` -> `/contact-us/`
   - `../../../home/` from deeply nested pages -> `/`
   - `raw_url` attributes already absolute — leave unchanged
   - `tel:`, `mailto:`, `http://`, `https://` links — leave unchanged
   - `#` anchor links — leave unchanged

2. **Fix CSS link paths** — update `<link>` tags:
   - `/Pages/desktop/...` -> `/_pages/desktop/...`
   - `/Pages/mobile/...` -> `/_pages/mobile/...`
   - `/Pages/tablet/...` -> `/_pages/tablet/...`

3. **Fix script src paths** — if any reference `/Pages/`:
   - Same pattern: `/Pages/` -> `/_pages/`

4. **Update canonical URLs** — if deploying to custom domain:
   - Find `<link rel="canonical"` and update href
   - Find `<meta property="og:url"` and update content

### Step 5: Fix Duda Runtime for Static Export

The Duda runtime (`runtime.js`) expects server-side platform dependencies that don't exist in a static export. Create `public/Scripts/duda-stubs.js` to provide them. See [references/duda-stubs.md](references/duda-stubs.md) for the full template.

The stubs file must be loaded **after** the device JS and **before** `runtime.js`. Run `scripts/fix_html.py` (Step 4) which automatically injects the correct `<script>` tag order into every HTML file.

**What duda-stubs.js provides:**

1. **`window.flexSite = true`** — Required for the layout module (chunk 105) to initialize the hamburger drawer manager correctly. On Duda flex sites, the hamburger button intentionally does NOT have the `.layout-drawer-hamburger` class. Instead, `window.flexSite` signals the layout module to use the guard function `s()`, which prevents a double-toggle bug where both chunk 847 (hamburger click handler) and LayoutDrawerManager attach competing click listeners.

2. **jQuery/$ stub** — The runtime expects `window.$` with `.DM`, `.dmrt`, `.layoutDevice`, `.fn` namespaces. The stub provides no-op implementations for all accessed methods.

3. **`window.rtCommonProps` / `window.commonProps`** — Empty objects to prevent "cannot read property of undefined" errors in widget initialization.

4. **`window.runtime.initWidgets()` trigger** — The static export doesn't call this automatically. The stub triggers it on DOMContentLoaded to load all widget chunks (animations, element transitions, scroll effects, etc.).

5. **SSR Accordion hydration stub** — Duda SSR accordions (`ssraccordion` widget type) depend on `window.waitForDeferred('ssrLibrariesLoaded', cb)` which never resolves in the static export because the Duda SSRRuntime React library is not included. The stub provides a lightweight click handler that:
   - Finds all `[data-auto="runtime-accordion-widget"]` containers
   - Adds click + keyboard handlers to `[data-grab="accordion-item-title-wrapper"]` elements
   - Toggles content `.dygwmn` div via `max-height` CSS transition (already defined in styled-components)
   - Implements `closeOthers` (one item open at a time per accordion)
   - Auto-expands first item on load (`firstExpanded: true`)

6. **SSR Image Slider hydration stub** — Same root cause as accordions. The stub:
   - Parses `<script data-role="hydration">` tags to extract SSR_IMAGE_SLIDER config (interval, slide count)
   - Drives auto-pagination via CSS `transform: translateX()` on the `[data-auto="slider-filmRole"]` element
   - Updates pagination bullet active states
   - Adds bullet click handlers for manual navigation

**Critical: Do NOT add `.layout-drawer-hamburger` class to the hamburger button HTML.** This causes a double-toggle bug where two click handlers both call `toggleNavMenus()`, canceling each other out. The flex-site architecture relies on `window.flexSite = true` + chunk 847 as the sole click handler.

### Step 6: Fix runtime.js publicPath

The Duda webpack runtime (`runtime.js`) has a hardcoded `publicPath` that points to Duda's editor path. This must be updated to `/Scripts/` for chunks to load from the correct location.

In `public/Scripts/runtime.js`, find and replace the publicPath assignment:
- **Find**: `a.p="/editor/apps/modules/runtime/"` (or similar Duda editor path)
- **Replace with**: `a.p="/Scripts/"`

This is critical — without it, all lazy-loaded chunks (animations, layout, widgets) will 404.

### Step 7: Create Edge Middleware

Create `middleware.ts` for server-side device detection. See [references/middleware.md](references/middleware.md) for the full template.

The middleware:
1. Skips static asset requests (`/Resources/`, `/Scripts/`, `/Style/`, `/_pages/`, `/_next/`, `/favicon`)
2. Parses User-Agent header to classify device as mobile/tablet/desktop
3. Maps clean URL to internal HTML file path using the route map
4. Rewrites request to `/_pages/{device}/{page-folder}/index.html`
5. Defaults to desktop for bots/crawlers (best for SEO)

Device detection rules:
- **Mobile**: User-Agent contains `iPhone`, `Android.*Mobile`, `iPod`, `BlackBerry`, `Windows Phone`, `Opera Mini`, `IEMobile`
- **Tablet**: User-Agent contains `iPad`, `Android` (without `Mobile`), `Tablet`, `Silk`
- **Desktop**: everything else (default — also serves search engine bots)

### Step 8: Create deployment config

Create `vercel.json`:
- Redirect `/home` and `/home/` to `/` (301 permanent)
- Cache headers for static assets (1 year immutable for Resources, Scripts, Style)

Create `public/robots.txt`:
- Allow all crawlers
- Disallow `/_pages/` and `/Scripts/`
- Reference sitemap URL

Update `sitemap.xml`:
- Replace original domain with deployment domain
- Copy to `public/sitemap.xml`

### Step 9: Update Schema.org data

Check `Scripts/desktop.js`, `Scripts/mobile.js`, `Scripts/tablet.js` for embedded structured data (Schema.org JSON-LD). Update any URLs referencing the old domain if deploying to a new domain.

### Step 10: Generate project documentation

Generate 3 documentation files customized for the project. See [references/documentation-templates.md](references/documentation-templates.md) for the full templates.

1. **README.md** — Project overview for developers
   - Replace placeholders: `{{PROJECT_NAME}}`, `{{DOMAIN}}`, `{{DUDA_SITE_ID}}`, `{{PAGE_COUNT}}`, `{{ROUTE_TABLE}}`, `{{SKILL_REPO_URL}}`
   - Fill in the route table from the route map built in Step 1
   - List all known issues encountered and their solutions

2. **GUIDE-SEO-DESIGN.md** — Collaboration guide for SEO & Design teams
   - Replace: `{{PROJECT_NAME}}`, `{{DOMAIN}}`, `{{PAGE_TABLE}}`, `{{SITEMAP_COUNT}}`, `{{FONT_NAME}}`, `{{FONT_WEIGHTS}}`
   - Fill in the page table with all pages and sitemap status
   - Update meta tag examples from the actual homepage `<head>`
   - Update slider info (count, slides per slider) from the actual homepage
   - Update font/breakpoint specs from the actual CSS

3. **GUIDE-DEVELOPER.md** — Developer workflow guide
   - Replace: `{{PROJECT_NAME}}`, `{{REPO_URL}}`, `{{SKILL_REPO_URL}}`, `{{ROUTE_TABLE}}`
   - Includes: AI-assisted dev setup (VS Code + Copilot with Claude Opus 4.6, Claude Code), branching strategy, PR process, Playwright testing, Figma design handoff workflow, deployment process

All 3 files should be committed to the repo root.

### Step 11: Test and deploy

1. `npm install` then `npm run dev`
2. Verify each page loads correctly at its clean URL
3. Test device switching via Chrome DevTools User-Agent override
4. Verify all navigation links, images, fonts, JS functionality
5. Run Playwright tests: `npx playwright test`
6. Run Lighthouse audit for SEO score
7. Deploy: `vercel deploy` or connect Git repo

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 on page load | Middleware route map missing a page | Add route to ROUTES object in middleware.ts |
| CSS not loading | Path still references `/Pages/` | Run fix_html.py or manually change to `/_pages/` |
| Images broken | URL-encoded spaces in filenames | Ensure `%20` encoding preserved in paths |
| Navigation loops | Relative links not fully converted | Check pages at different nesting depths |
| Form not working | External embed blocked by CORS | Whitelist Vercel domain in form provider settings |
| Flash of wrong layout | Client JS overriding device type | Ensure device JS files match served version |
| Fonts not loading | @font-face paths incorrect | Verify `/Resources/files/` path in CSS |
| Animations not playing | runtime.js publicPath wrong | Change `a.p=` in runtime.js to `a.p="/Scripts/"` |
| Hamburger opens then closes | Double-toggle: two click handlers | Do NOT add `.layout-drawer-hamburger` class; use `window.flexSite = true` only |
| Hamburger does nothing | `window.layoutApp` undefined | Ensure duda-stubs.js loaded, `window.flexSite = true` set, publicPath fixed |
| FAQ accordion not clickable | SSR hydration never fires | duda-stubs.js accordion stub handles this automatically |
| Image slider stuck on first | SSR hydration never fires | duda-stubs.js slider stub handles this automatically |
| Chunk loading 404 | publicPath points to Duda editor | Fix `a.p=` in runtime.js to `/Scripts/` |

## SEO Checklist

- [ ] Each page has unique `<title>` and `<meta name="description">`
- [ ] Canonical URLs point to correct clean URLs on deployment domain
- [ ] `robots.txt` allows crawling of public pages, blocks internal paths
- [ ] `sitemap.xml` lists all indexed pages with correct domain
- [ ] Schema.org LocalBusiness structured data has correct URL
- [ ] `noindex` pages (thank-you, privacy-policy, terms-conditions) have `<meta name="robots" content="noindex">`
- [ ] Desktop version served to bots (most content-complete)
- [ ] Open Graph and Twitter Card meta tags have correct URLs
- [ ] `<meta name="viewport">` present on all pages
- [ ] All internal links use clean absolute paths (not relative)

## Documentation Checklist

- [ ] `README.md` created with project-specific migration details
- [ ] `GUIDE-SEO-DESIGN.md` created with page list, meta tag examples, request templates
- [ ] `GUIDE-DEVELOPER.md` created with AI setup, branching, PR process, Playwright tests
- [ ] All `{{PLACEHOLDER}}` values replaced with actual project data
- [ ] Meta tag examples filled from actual homepage `<head>` tags
- [ ] Slider info filled from homepage analysis
- [ ] Font/breakpoint specs match actual CSS
- [ ] All 3 docs committed to repo root
