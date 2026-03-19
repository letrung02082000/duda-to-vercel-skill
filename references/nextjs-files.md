# Next.js Project Files for Duda Conversion

## package.json

```json
{
  "name": "duda-vercel-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "typescript": "^5.7.0"
  }
}
```

## next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // No special config needed — middleware handles routing
  // Static assets served directly from public/
}

module.exports = nextConfig
```

## tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": false,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

## app/layout.tsx

```tsx
export const metadata = {
  // Metadata handled by individual HTML pages, not Next.js
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return children
}
```

## app/page.tsx

```tsx
// Placeholder — middleware rewrites all routes to static HTML files in public/_pages/
// This file exists only to satisfy Next.js App Router requirements
export default function Page() {
  return null
}
```

## vercel.json

Customize redirects and cache headers per project:

```json
{
  "redirects": [
    { "source": "/home", "destination": "/", "permanent": true },
    { "source": "/home/", "destination": "/", "permanent": true }
  ],
  "headers": [
    {
      "source": "/Resources/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/Scripts/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/Style/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

## public/robots.txt

Template — replace `{DOMAIN}` with actual deployment domain:

```
User-agent: *
Allow: /

Disallow: /_pages/
Disallow: /Scripts/

Sitemap: https://{DOMAIN}/sitemap.xml
```
