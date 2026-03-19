# Edge Middleware Template for Duda Device Detection

## middleware.ts

Place at the project root (same level as `app/` and `public/`).

Customize the `ROUTES` object to match the site's pages.

```typescript
import { NextRequest, NextResponse } from 'next/server'

// Map clean URL paths to page folder paths inside /_pages/{device}/
// Key: URL path (with leading slash, no trailing slash)
// Value: folder path under /_pages/{device}/
const ROUTES: Record<string, string> = {
  '/': 'home',
  '/about-us': 'about-us',
  '/contact-us': 'contact-us',
  '/thank-you': 'thank-you',
  '/privacy-policy': 'privacy-policy',
  '/terms-conditions': 'terms-conditions',
  // Add service/location pages as needed:
  // '/texas/cypress/towing-services': 'texas/cypress/towing-services',
}

type DeviceType = 'desktop' | 'mobile' | 'tablet'

function detectDevice(userAgent: string): DeviceType {
  const ua = userAgent.toLowerCase()

  // Mobile detection (must check before tablet — Android phones have 'Mobile')
  if (
    /iphone|ipod|blackberry|windows phone|opera mini|iemobile/.test(ua) ||
    (/android/.test(ua) && /mobile/.test(ua))
  ) {
    return 'mobile'
  }

  // Tablet detection
  if (
    /ipad|tablet|silk/.test(ua) ||
    (/android/.test(ua) && !/mobile/.test(ua))
  ) {
    return 'tablet'
  }

  // Default: desktop (also serves bots/crawlers for best SEO)
  return 'desktop'
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Normalize: strip trailing slash (except root)
  const normalizedPath = pathname === '/' ? '/' : pathname.replace(/\/$/, '')

  // Check if this path matches a known route
  const pagePath = ROUTES[normalizedPath]
  if (!pagePath) {
    // Not a known page route — let Next.js handle (404 or static file)
    return NextResponse.next()
  }

  // Detect device from User-Agent
  const userAgent = request.headers.get('user-agent') || ''
  const device = detectDevice(userAgent)

  // Rewrite to the correct device-specific HTML file
  const htmlPath = `/_pages/${device}/${pagePath}/index.html`
  const url = request.nextUrl.clone()
  url.pathname = htmlPath

  return NextResponse.rewrite(url)
}

export const config = {
  // Only run middleware on page routes, skip static assets
  matcher: [
    '/((?!_pages|Resources|Scripts|Style|api|_next|favicon\\.ico|robots\\.txt|sitemap\\.xml).*)',
  ],
}
```

## How it works

1. Request comes in for `/about-us`
2. Middleware matcher confirms it's not a static asset path
3. `ROUTES['/about-us']` resolves to `'about-us'`
4. User-Agent parsed: e.g., iPhone -> `'mobile'`
5. `NextResponse.rewrite()` internally serves `/_pages/mobile/about-us/index.html`
6. Browser URL stays as `/about-us` (rewrite, not redirect)

## Customization

### Adding routes

Add entries to `ROUTES` for each page in the Duda export:

```typescript
const ROUTES: Record<string, string> = {
  '/': 'home',
  '/about-us': 'about-us',
  '/services/plumbing': 'services/plumbing',  // Nested page example
  // ...
}
```

### Building ROUTES dynamically

To auto-generate from directory listing:

```bash
# List all page folders under Pages/desktop/
find Pages/desktop -name "index.html" -printf '%P\n' | sed 's|/index.html||'
```

Each result is a value for ROUTES. The key is the clean URL:
- `home` -> `/`
- `about-us` -> `/about-us`
- `texas/cypress/towing-services` -> `/texas/cypress/towing-services`

### Custom 404 handling

Add a catch-all at the end of middleware to serve a custom 404 page:

```typescript
// After ROUTES lookup fails:
if (!pagePath) {
  // Option 1: Let Next.js default 404 handle it
  return NextResponse.next()

  // Option 2: Serve a custom 404 HTML from your export
  // const device = detectDevice(request.headers.get('user-agent') || '')
  // const url = request.nextUrl.clone()
  // url.pathname = `/_pages/${device}/404/index.html`
  // return NextResponse.rewrite(url)
}
```

### Force specific device (debugging)

Add query parameter support for testing:

```typescript
// At the top of middleware function, before detectDevice:
const forceDevice = request.nextUrl.searchParams.get('device')
if (forceDevice && ['desktop', 'mobile', 'tablet'].includes(forceDevice)) {
  device = forceDevice as DeviceType
}
```

Then test with: `https://your-site.vercel.app/about-us?device=mobile`
