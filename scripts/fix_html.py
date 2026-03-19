#!/usr/bin/env python3
"""
Fix HTML files in a restructured Duda export for Vercel deployment.

Usage:
    python fix_html.py <pages-dir> [--home-folder home] [--domain DOMAIN]

Example:
    python fix_html.py ./public/_pages --home-folder home --domain mysite.vercel.app

Fixes applied to every HTML file:
1. Convert relative navigation links (href) to absolute paths
2. Update CSS <link> paths: /Pages/ -> /_pages/
3. Update any /Pages/ references in scripts or inline styles
4. Optionally update canonical/OG URLs to new domain

Arguments:
    pages-dir     Path to the _pages directory (e.g., ./public/_pages)
    --home-folder Name of the home page folder (default: "home")
    --domain      Deployment domain for canonical URL updates (optional)
"""

import argparse
import re
from pathlib import Path, PurePosixPath


DEVICES = ["desktop", "mobile", "tablet"]


def resolve_relative_href(href: str, page_rel_path: str, home_folder: str) -> str:
    """
    Resolve a relative href to an absolute URL path.

    Args:
        href: The relative href value (e.g., "../contact-us/", "./#quote")
        page_rel_path: Page path relative to device root (e.g., "home", "texas/cypress/towing-services")
        home_folder: Name of the home page folder (maps to "/")

    Returns:
        Absolute URL path (e.g., "/contact-us/", "/#quote")
    """
    # Split anchor from path
    anchor = ""
    path_part = href
    if "#" in href:
        idx = href.index("#")
        path_part = href[:idx]
        anchor = href[idx:]

    if not path_part or path_part == "./":
        # Self-reference — resolve to current page's clean URL
        if page_rel_path == home_folder:
            return "/" + anchor
        return "/" + page_rel_path + "/" + anchor

    # Resolve relative path against current page's directory
    current_dir = PurePosixPath(page_rel_path)
    resolved = current_dir / path_part
    # Normalize (resolve ..)
    parts = []
    for part in resolved.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)

    resolved_path = "/".join(parts)

    # Strip trailing slash for comparison, then determine clean URL
    clean = resolved_path.rstrip("/")

    if clean == home_folder:
        return "/" + anchor

    if clean:
        return "/" + clean + "/" + anchor

    return "/" + anchor


def should_fix_href(href: str) -> bool:
    """Check if an href value is a relative navigation link that needs fixing."""
    if not href:
        return False
    # Skip absolute URLs, tel:, mailto:, javascript:, anchors-only, already-absolute
    if href.startswith(("http://", "https://", "tel:", "mailto:", "javascript:", "#", "/")):
        return False
    # It's a relative link — needs fixing
    return True


def fix_html_content(content: str, page_rel_path: str, home_folder: str, domain: str = "", device: str = "") -> str:
    """Fix all links in an HTML file's content."""

    # 1. Fix /Pages/ -> /_pages/ (CSS links, script src, any reference)
    content = content.replace('"/Pages/', '"/_pages/')
    content = content.replace("'/Pages/", "'/_pages/")
    content = content.replace("(/Pages/", "(/_pages/")

    # 2. Fix relative navigation hrefs
    def replace_href(match: re.Match) -> str:
        prefix = match.group(1)  # 'href="' or "href='"
        href = match.group(2)
        suffix = match.group(3)  # closing quote

        if not should_fix_href(href):
            return match.group(0)

        absolute = resolve_relative_href(href, page_rel_path, home_folder)
        return f"{prefix}{absolute}{suffix}"

    # Match href="..." and href='...'
    content = re.sub(
        r'''(href=["'])([^"']*)(["'])''',
        replace_href,
        content
    )

    # 3. Optionally update canonical and OG URLs
    if domain:
        # Update canonical
        content = re.sub(
            r'(<link\s+rel="canonical"\s+href=")([^"]*)',
            lambda m: m.group(1) + _build_canonical(m.group(2), domain, page_rel_path, home_folder),
            content,
        )
        # Update og:url
        content = re.sub(
            r'(<meta\s+property="og:url"\s+content=")([^"]*)',
            lambda m: m.group(1) + _build_canonical(m.group(2), domain, page_rel_path, home_folder),
            content,
        )

    # 4. Inject duda-stubs.js between device JS and runtime.js
    #    Expected load order: {device}.js -> duda-stubs.js -> runtime.js
    if device:
        device_script_tag = f'<script src="/Scripts/{device}.js">'
        stubs_tag = '<script src="/Scripts/duda-stubs.js"> </script>\n'
        runtime_tag = '<script src="/Scripts/runtime.js">'

        # Only inject if stubs not already present and both device/runtime scripts exist
        if 'duda-stubs.js' not in content and device_script_tag in content and runtime_tag in content:
            # Insert stubs script right before runtime.js
            content = content.replace(
                f' {runtime_tag}',
                f' {stubs_tag} {runtime_tag}'
            )

    return content


def _build_canonical(old_url: str, domain: str, page_rel_path: str, home_folder: str) -> str:
    """Build canonical URL for the page."""
    if page_rel_path == home_folder:
        return f"https://{domain}/"
    return f"https://{domain}/{page_rel_path}"


def get_page_rel_path(html_path: Path, pages_dir: Path) -> tuple[str, str]:
    """
    Get the page's relative path from the device root.

    Returns: (device, page_rel_path)
    Example: ("desktop", "texas/cypress/towing-services")
    """
    rel = html_path.parent.relative_to(pages_dir)
    parts = rel.parts  # e.g., ("desktop", "texas", "cypress", "towing-services")
    device = parts[0]
    page_rel = "/".join(parts[1:])
    return device, page_rel


def fix_runtime_publicpath(runtime_path: Path) -> None:
    """Fix webpack publicPath in runtime.js to point to /Scripts/."""
    if not runtime_path.exists():
        print(f"  SKIP runtime.js not found at {runtime_path}")
        return

    content = runtime_path.read_text(encoding="utf-8")

    # Match a.p="<any-path>" and replace with a.p="/Scripts/"
    fixed, count = re.subn(r'a\.p="[^"]*"', 'a.p="/Scripts/"', content)

    if count > 0 and fixed != content:
        runtime_path.write_text(fixed, encoding="utf-8")
        print(f"  FIXED runtime.js publicPath ({count} replacement(s))")
    else:
        print(f"  OK    runtime.js publicPath (already correct)")


def create_duda_stubs(stubs_path: Path) -> None:
    """Create duda-stubs.js if it doesn't exist."""
    if stubs_path.exists():
        print(f"  OK    duda-stubs.js already exists")
        return

    # Read the template from references/duda-stubs.md (extract code block)
    # Fallback: generate minimal stubs inline
    stubs_content = '''\
/* Duda static export stubs - provides missing platform dependencies */
(function() {
  window.rtCommonProps = window.rtCommonProps || {};
  window.commonProps = window.commonProps || {};
  window.flexSite = true;

  if (!window.$) {
    var noop = function() { return window.$; };
    window.$ = function() { return { on: noop, off: noop, trigger: noop, find: noop, each: noop, addClass: noop, removeClass: noop, css: noop, attr: noop, data: noop, html: noop, text: noop, append: noop, remove: noop, length: 0 }; };
    window.$.DM = {
      events: { on: noop, off: noop, trigger: noop },
      afterAjaxGeneralInits: noop, hydrateNonSSRWidgets: noop, initNonAjaxPopups: noop,
      insideEditor: function() { return false; }, isHrefAliasCurrent: function() { return false; },
      isPreview: false, openPopupLink: noop, scrollToAnchor: noop, scrollToAnchorFromLinkClickEvent: noop
    };
    window.$.dmrt = {
      components: {
        popupService: { initializeCloseButtons: noop, cleanCloseButtons: noop, displayPopup: noop, initializeSSR: noop },
        imageslider: { goToSlideBySrc: noop }
      }
    };
    window.$.layoutDevice = { type: window._currentDevice || 'desktop' };
    window.$.fn = {};
  }

  function initAccordions() {
    document.querySelectorAll('[data-auto="runtime-accordion-widget"]').forEach(function(accordion) {
      var items = accordion.querySelectorAll('[data-grab="accordion-item-container"]');
      items.forEach(function(item, index) {
        var tw = item.querySelector('[data-grab="accordion-item-title-wrapper"]');
        var cd = item.querySelector('.dygwmn');
        if (!tw || !cd) return;
        var bars = item.querySelectorAll('[data-grab="accordion-item-arrow"] > div > div');
        if (index === 0) cd.style.maxHeight = cd.scrollHeight + 'px';
        function toggle() {
          var open = cd.style.maxHeight && cd.style.maxHeight !== '0px';
          if (open) { cd.style.maxHeight = '0px'; setArrow(bars, false); }
          else {
            items.forEach(function(o) {
              var oc = o.querySelector('.dygwmn');
              if (oc && oc !== cd && oc.style.maxHeight && oc.style.maxHeight !== '0px') {
                oc.style.maxHeight = '0px';
                setArrow(o.querySelectorAll('[data-grab="accordion-item-arrow"] > div > div'), false);
              }
            });
            cd.style.maxHeight = cd.scrollHeight + 'px'; setArrow(bars, true);
          }
        }
        tw.addEventListener('click', toggle);
        tw.addEventListener('keydown', function(e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
      });
    });
  }
  function setArrow(bars, open) {
    if (bars.length < 2) return;
    bars[0].style.transform = open ? 'rotate(90deg)' : 'rotate(-90deg)';
    bars[1].style.transform = open ? 'rotate(90deg)' : 'rotate(-90deg)';
    bars[1].style.opacity = open ? '0' : '1';
  }

  function initSliders() {
    document.querySelectorAll('script[data-role="hydration"]').forEach(function(script) {
      var text = script.textContent;
      if (text.indexOf('SSR_IMAGE_SLIDER') === -1) return;
      try {
        var m = 'initiateWidget(', s = text.indexOf(m);
        if (s === -1) return; s += m.length;
        var d = 0, e = s;
        for (var i = s; i < text.length; i++) { if (text[i] === '{') d++; if (text[i] === '}') { d--; if (d === 0) { e = i + 1; break; } } }
        var cfg = JSON.parse(text.substring(s, e)), p = cfg.props;
        if (!p) return;
        var el = document.getElementById(cfg.id); if (!el) return;
        if (p.slidesData) {
          var mm = {};
          p.slidesData.forEach(function(sl) { mm[sl.uuid] = sl.media || {}; });
          el.querySelectorAll('[data-auto^="ssr-slide-"]').forEach(function(slot) {
            var uuid = slot.getAttribute('data-auto').replace('ssr-slide-', '');
            var info = mm[uuid]; if (!info || !info.imgSrc) return;
            var me = slot.querySelector('[data-grab="slide-media"]');
            if (!me || me.tagName === 'IMG') return;
            var img = document.createElement('img');
            img.setAttribute('data-grab', 'slide-media');
            img.src = decodeURIComponent(info.imgSrc);
            if (info.alt) img.alt = info.alt;
            img.style.cssText = 'object-fit:cover;display:block;width:100%;height:100%';
            me.parentNode.replaceChild(img, me);
          });
        }
        var fr = el.querySelector('[data-auto="slider-filmRole"]'); if (!fr) return;
        var ts = fr.children.length; if (ts <= 1) return;
        if (!p.autoPagination || !p.autoPagination.on) return;
        var bl = el.querySelectorAll('[data-grab^="pagination-button-bullet"]');
        var np = bl.length || ts, ci = 0, ac = '', ic = '';
        bl.forEach(function(b) { if (b.getAttribute('data-grab').indexOf('active') !== -1) ac = b.className; else if (!ic) ic = b.className; });
        function go(idx) {
          ci = idx; fr.style.transform = 'translateX(' + -(idx * (100 / ts)) + '%)';
          bl.forEach(function(b, bi) {
            b.setAttribute('data-grab', bi === idx ? 'pagination-button-bullet active' : 'pagination-button-bullet');
            b.className = bi === idx ? ac : ic;
          });
        }
        bl.forEach(function(b, bi) { b.addEventListener('click', function() { go(bi); }); });
        setInterval(function() { go((ci + 1) % np); }, (p.autoPagination.intervalInSeconds || 3) * 1000);
      } catch (ex) {}
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    if (window.runtime && typeof window.runtime.initWidgets === 'function') window.runtime.initWidgets();
    initAccordions();
    initSliders();
  });
})();
'''
    stubs_path.write_text(stubs_content, encoding="utf-8")
    print(f"  CREATED duda-stubs.js")


def process_files(pages_dir: Path, home_folder: str, domain: str) -> None:
    """Process all HTML files in the _pages directory."""
    html_files = sorted(pages_dir.rglob("*.html"))

    if not html_files:
        print(f"No HTML files found in {pages_dir}")
        return

    # Fix runtime.js publicPath if Scripts dir exists at the same level
    scripts_dir = pages_dir.parent / "Scripts"
    if scripts_dir.exists():
        fix_runtime_publicpath(scripts_dir / "runtime.js")
        create_duda_stubs(scripts_dir / "duda-stubs.js")

    print(f"Processing {len(html_files)} HTML files in {pages_dir}\n")

    for html_path in html_files:
        device, page_rel = get_page_rel_path(html_path, pages_dir)
        if device not in DEVICES:
            print(f"  SKIP {html_path.relative_to(pages_dir)} (unknown device: {device})")
            continue

        content = html_path.read_text(encoding="utf-8")
        fixed = fix_html_content(content, page_rel, home_folder, domain, device)

        if fixed != content:
            html_path.write_text(fixed, encoding="utf-8")
            print(f"  FIXED {html_path.relative_to(pages_dir)}")
        else:
            print(f"  OK    {html_path.relative_to(pages_dir)} (no changes)")

    print("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix HTML files in Duda export for Vercel")
    parser.add_argument("pages_dir", type=Path, help="Path to _pages directory")
    parser.add_argument("--home-folder", default="home", help="Name of home page folder (default: home)")
    parser.add_argument("--domain", default="", help="Deployment domain for canonical URL updates")
    args = parser.parse_args()

    pages_dir = args.pages_dir.resolve()
    if not pages_dir.exists():
        print(f"Error: directory not found: {pages_dir}")
        exit(1)

    process_files(pages_dir, args.home_folder, args.domain)
