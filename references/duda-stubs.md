# Duda Static Export Stubs (duda-stubs.js)

## Purpose

Provides missing Duda platform dependencies for static exports. Without this file, the Duda webpack runtime (`runtime.js`) throws errors and many interactive features (hamburger nav, animations, accordions, image sliders) don't work.

## Script Load Order

The device JS, stubs, and runtime must load in this exact order in every HTML file:

```html
<script src="/Scripts/{device}.js"></script>
<script src="/Scripts/duda-stubs.js"></script>
<script src="/Scripts/runtime.js"></script>
```

Where `{device}` is `desktop`, `mobile`, or `tablet` matching the HTML version.

## Template

Save as `public/Scripts/duda-stubs.js`:

```javascript
/* Duda static export stubs - provides missing platform dependencies */
(function() {
  // Stub rtCommonProps (server-side config not available in static export)
  window.rtCommonProps = window.rtCommonProps || {};
  window.commonProps = window.commonProps || {};

  // Layout module needs this to initialize hamburger drawer manager.
  // CRITICAL: Do NOT add .layout-drawer-hamburger class to the hamburger button HTML.
  // The flex-site architecture uses window.flexSite + chunk 847 as the sole click handler.
  // Adding the class causes a double-toggle bug (two handlers both call toggleNavMenus).
  window.flexSite = true;

  // Minimal jQuery/$ stub - Duda runtime expects window.$ with DM namespace
  if (!window.$) {
    var noop = function() { return window.$; };
    window.$ = function() { return { on: noop, off: noop, trigger: noop, find: noop, each: noop, addClass: noop, removeClass: noop, css: noop, attr: noop, data: noop, html: noop, text: noop, append: noop, remove: noop, length: 0 }; };
    window.$.DM = {
      events: { on: noop, off: noop, trigger: noop },
      afterAjaxGeneralInits: noop,
      hydrateNonSSRWidgets: noop,
      initNonAjaxPopups: noop,
      insideEditor: function() { return false; },
      isHrefAliasCurrent: function() { return false; },
      isPreview: false,
      openPopupLink: noop,
      scrollToAnchor: noop,
      scrollToAnchorFromLinkClickEvent: noop
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

  // === SSR Accordion Hydration Stub ===
  // Duda SSR accordions use waitForDeferred('ssrLibrariesLoaded') which never resolves
  // in static exports. This provides lightweight click handlers directly.
  function initAccordions() {
    var accordions = document.querySelectorAll('[data-auto="runtime-accordion-widget"]');
    accordions.forEach(function(accordion) {
      var items = accordion.querySelectorAll('[data-grab="accordion-item-container"]');
      items.forEach(function(item, index) {
        var titleWrapper = item.querySelector('[data-grab="accordion-item-title-wrapper"]');
        var contentDiv = item.querySelector('.dygwmn');
        if (!titleWrapper || !contentDiv) return;

        var arrowBars = item.querySelectorAll('[data-grab="accordion-item-arrow"] > div > div');

        // Expand first item by default (firstExpanded: true)
        if (index === 0) {
          contentDiv.style.maxHeight = contentDiv.scrollHeight + 'px';
        }

        function toggle() {
          var isOpen = contentDiv.style.maxHeight && contentDiv.style.maxHeight !== '0px';
          if (isOpen) {
            contentDiv.style.maxHeight = '0px';
            setArrow(arrowBars, false);
          } else {
            // Close others in same accordion (closeOthers: true)
            items.forEach(function(other) {
              var otherContent = other.querySelector('.dygwmn');
              if (otherContent && otherContent !== contentDiv && otherContent.style.maxHeight && otherContent.style.maxHeight !== '0px') {
                otherContent.style.maxHeight = '0px';
                setArrow(other.querySelectorAll('[data-grab="accordion-item-arrow"] > div > div'), false);
              }
            });
            contentDiv.style.maxHeight = contentDiv.scrollHeight + 'px';
            setArrow(arrowBars, true);
          }
        }

        titleWrapper.addEventListener('click', toggle);
        titleWrapper.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
        });
      });
    });
  }

  function setArrow(bars, isOpen) {
    if (bars.length < 2) return;
    bars[0].style.transform = isOpen ? 'rotate(90deg)' : 'rotate(-90deg)';
    bars[1].style.transform = isOpen ? 'rotate(90deg)' : 'rotate(-90deg)';
    bars[1].style.opacity = isOpen ? '0' : '1';
  }

  // === SSR Image Slider Hydration Stub ===
  // Parses config from <script data-role="hydration"> tags and drives auto-pagination.
  function initSliders() {
    var scripts = document.querySelectorAll('script[data-role="hydration"]');
    scripts.forEach(function(script) {
      var text = script.textContent;
      if (text.indexOf('SSR_IMAGE_SLIDER') === -1) return;

      try {
        var marker = 'initiateWidget(';
        var start = text.indexOf(marker);
        if (start === -1) return;
        start += marker.length;
        var depth = 0, end = start;
        for (var i = start; i < text.length; i++) {
          if (text[i] === '{') depth++;
          if (text[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
        }
        var config = JSON.parse(text.substring(start, end));
        var props = config.props;
        if (!props) return;

        var widgetId = config.id;
        var el = document.getElementById(widgetId);
        if (!el) return;

        // Inject missing images: Duda SSR only pre-renders <img> for visible slots
        // (slotsInFrame). Remaining slots are empty <div> placeholders.
        if (props.slidesData) {
          var mediaMap = {};
          props.slidesData.forEach(function(slide) {
            mediaMap[slide.uuid] = slide.media || {};
          });
          el.querySelectorAll('[data-auto^="ssr-slide-"]').forEach(function(slot) {
            var uuid = slot.getAttribute('data-auto').replace('ssr-slide-', '');
            var info = mediaMap[uuid];
            if (!info || !info.imgSrc) return;
            var mediaEl = slot.querySelector('[data-grab="slide-media"]');
            if (!mediaEl || mediaEl.tagName === 'IMG') return;
            var img = document.createElement('img');
            img.setAttribute('data-grab', 'slide-media');
            img.src = decodeURIComponent(info.imgSrc);
            if (info.alt) img.alt = info.alt;
            img.style.cssText = 'object-fit:cover;display:block;width:100%;height:100%';
            mediaEl.parentNode.replaceChild(img, mediaEl);
          });
        }

        var filmRole = el.querySelector('[data-auto="slider-filmRole"]');
        if (!filmRole) return;

        var totalSlots = filmRole.children.length;
        if (totalSlots <= 1) return;

        // Auto-pagination
        if (!props.autoPagination || !props.autoPagination.on) return;
        var interval = (props.autoPagination.intervalInSeconds || 3) * 1000;

        var bullets = el.querySelectorAll('[data-grab^="pagination-button-bullet"]');
        var numPages = bullets.length || totalSlots;
        var currentIndex = 0;

        var activeBulletClass = '', inactiveBulletClass = '';
        bullets.forEach(function(b) {
          if (b.getAttribute('data-grab').indexOf('active') !== -1) {
            activeBulletClass = b.className;
          } else if (!inactiveBulletClass) {
            inactiveBulletClass = b.className;
          }
        });

        function goToSlide(idx) {
          currentIndex = idx;
          var pct = -(idx * (100 / totalSlots));
          filmRole.style.transform = 'translateX(' + pct + '%)';
          bullets.forEach(function(b, bi) {
            if (bi === idx) {
              b.setAttribute('data-grab', 'pagination-button-bullet active');
              b.className = activeBulletClass;
            } else {
              b.setAttribute('data-grab', 'pagination-button-bullet');
              b.className = inactiveBulletClass;
            }
          });
        }

        bullets.forEach(function(b, bi) {
          b.addEventListener('click', function() { goToSlide(bi); });
        });

        setInterval(function() {
          goToSlide((currentIndex + 1) % numPages);
        }, interval);
      } catch (e) { /* skip broken slider config */ }
    });
  }

  // Trigger widget+animation initialization — static export doesn't call these
  document.addEventListener('DOMContentLoaded', function() {
    if (window.runtime) {
      if (typeof window.runtime.initWidgets === 'function') {
        window.runtime.initWidgets();
      }
    }
    // Initialize SSR widgets that depend on never-resolved ssrLibrariesLoaded deferred
    initAccordions();
    initSliders();
  });
})();
```

## How It Works

### Hamburger Navigation

The Duda runtime has two systems for hamburger clicks:

1. **Chunk 847**: Attaches click to all `.hamburgerButton` elements → `window.layoutApp.toggleNavMenus()`
2. **LayoutDrawerManager** (chunk 105): Conditionally attaches click to `.layout-drawer-hamburger` → `this.toggleNavMenus()`

A guard function `s() = window.flexSite && !querySelector(".layout-drawer-hamburger")` controls whether the LayoutDrawerManager adds its own handler.

With `window.flexSite = true` and NO `.layout-drawer-hamburger` class on the button:
- `s()` returns `true` → LayoutDrawerManager skips its own click listener
- `initLayout()` still enters the correct branch: `querySelector(".layout-drawer-hamburger") || s()` → `null || true`
- Chunk 847 is the sole handler → one toggle per click → works correctly

**WARNING**: Adding `.layout-drawer-hamburger` to the button creates a double-toggle bug (two handlers both toggle, canceling each other out).

### SSR Widget Hydration

Duda SSR widgets (accordions, image sliders) use a deferred-loading pattern:
```javascript
window?.waitForDeferred?.('ssrLibrariesLoaded', () => {
  window.SSRRuntime.RuntimeReactHelpers.initiateWidget({type: "SSR_ACCORDION", ...})
})
```

The `ssrLibrariesLoaded` deferred is defined in device JS files but never resolved in static exports (the SSRRuntime React library is not included). The stubs bypass this entirely with direct DOM manipulation.

### Widget Initialization

`window.runtime.initWidgets()` is normally called by Duda's server-side rendering pipeline. In static exports, nothing triggers it. The stubs call it on DOMContentLoaded, which loads all widget chunks (animations, element transitions, scroll effects, parallax, etc.).
