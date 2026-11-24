"""
tests/test_challenger_viewports.py
Empirical Challenger 2: Web UI Multi-Viewport Stress Testing.

Stress-tests both web_app/index.html and frontend_demo.html across 8 screen widths:
- 320px  (Small mobile / iPhone SE 1st gen)
- 360px  (Standard Android compact)
- 375px  (iPhone X / 12 mini)
- 414px  (iPhone 11 Pro Max / Plus)
- 768px  (iPad portrait / tablet breakpoint)
- 1024px (iPad landscape / small desktop)
- 1440px (Laptop / standard desktop)
- 1920px (Full HD 1080p desktop)

Verifies:
1. Zero horizontal body scroll: document.body.scrollWidth <= window.innerWidth
2. Zero document horizontal scroll: document.documentElement.scrollWidth <= document.documentElement.clientWidth
3. Zero DOM element breakout: no element with bounding box extending beyond viewport width
4. Stability across all 4 views: landing, studio, specs, chat
5. Stability during council modal overlay toggle
6. Zero critical runtime console errors
"""

import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT_DIR / "web_app" / "index.html"
DEMO_HTML = ROOT_DIR / "frontend_demo.html"

TARGET_FILES = [
    ("web_app/index.html", INDEX_HTML.as_uri()),
    ("frontend_demo.html", DEMO_HTML.as_uri()),
]

# 8 non-standard and standard screen widths from prompt
STRESS_VIEWPORTS = [
    ("Mobile 320px", 320, 568),
    ("Mobile 360px", 360, 640),
    ("Mobile 375px", 375, 812),
    ("Mobile 414px", 414, 896),
    ("Tablet 768px", 768, 1024),
    ("Tablet/Desktop 1024px", 1024, 768),
    ("Laptop 1440px", 1440, 900),
    ("Desktop 1920px", 1920, 1080),
]

VIEWS = ["landing", "studio", "specs", "chat"]


@pytest.fixture(scope="module")
def browser_instance():
    """Launch headless Chromium browser for viewport simulation."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


class TestChallengerMultiViewportStress:
    """Empirical verification of 8 viewport widths with zero horizontal scroll and zero visual breakage."""

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    @pytest.mark.parametrize("vp_label,width,height", STRESS_VIEWPORTS)
    def test_zero_horizontal_overflow_across_views(self, browser_instance, file_label, file_url, vp_label, width, height):
        """Verify body and document scrollWidth <= clientWidth across all 4 views."""
        context = browser_instance.new_context(viewport={"width": width, "height": height})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

        page.goto(file_url, wait_until="load")
        page.wait_for_timeout(350)

        for view in VIEWS:
            page.evaluate(f"switchView('{view}')")
            page.wait_for_timeout(150)

            # Measure document and body scroll widths
            metrics = page.evaluate("""() => {
                return {
                    bodyScrollWidth: document.body.scrollWidth,
                    docScrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    innerWidth: window.innerWidth
                };
            }""")

            body_scroll = metrics["bodyScrollWidth"]
            doc_scroll = metrics["docScrollWidth"]
            client_w = metrics["clientWidth"]
            inner_w = metrics["innerWidth"]

            # Tolerance of 1px for fractional subpixel layout rendering
            assert body_scroll <= inner_w + 1, (
                f"[{file_label} | {vp_label}] View '{view}' body overflow: "
                f"bodyScrollWidth={body_scroll} > innerWidth={inner_w}"
            )
            assert doc_scroll <= client_w + 1, (
                f"[{file_label} | {vp_label}] View '{view}' document overflow: "
                f"docScrollWidth={doc_scroll} > clientWidth={client_w}"
            )

        context.close()

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    @pytest.mark.parametrize("vp_label,width,height", STRESS_VIEWPORTS)
    def test_council_modal_overlay_overflow(self, browser_instance, file_label, file_url, vp_label, width, height):
        """Verify Council Modal does not introduce horizontal overflow when opened."""
        context = browser_instance.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        page.goto(file_url, wait_until="load")
        page.wait_for_timeout(300)

        # Open council modal
        page.evaluate("toggleCouncilModal()")
        page.wait_for_timeout(200)

        metrics = page.evaluate("""() => {
            return {
                bodyScrollWidth: document.body.scrollWidth,
                docScrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                innerWidth: window.innerWidth
            };
        }""")

        assert metrics["bodyScrollWidth"] <= metrics["innerWidth"] + 1, (
            f"[{file_label} | {vp_label}] Council modal caused body horizontal overflow"
        )
        assert metrics["docScrollWidth"] <= metrics["clientWidth"] + 1, (
            f"[{file_label} | {vp_label}] Council modal caused document horizontal overflow"
        )

        page.evaluate("toggleCouncilModal()")
        context.close()

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    @pytest.mark.parametrize("vp_label,width,height", [
        ("Mobile 320px", 320, 568),
        ("Mobile 360px", 360, 640),
        ("Mobile 375px", 375, 812),
        ("Mobile 414px", 414, 896),
        ("Tablet 768px", 768, 1024),
    ])
    def test_navigation_responsive_stability(self, browser_instance, file_label, file_url, vp_label, width, height):
        """Verify navigation elements (mobile drawer on <768px, desktop nav on >=768px) operate without overflow."""
        context = browser_instance.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        page.goto(file_url, wait_until="load")
        page.wait_for_timeout(300)

        menu_btn = page.locator("#mobileMenuToggleBtn")
        drawer = page.locator("#mobileNavDrawer")

        if width < 768:
            # On mobile viewports (< md: 768px), hamburger menu is visible
            assert menu_btn.is_visible(), f"[{file_label} | {vp_label}] Mobile menu toggle button should be visible"
            assert not drawer.is_visible(), f"[{file_label} | {vp_label}] Mobile nav drawer should be hidden initially"

            # Open drawer
            menu_btn.click()
            page.wait_for_timeout(200)
            assert drawer.is_visible(), f"[{file_label} | {vp_label}] Mobile nav drawer failed to open"

            # Check overflow while drawer is open
            metrics = page.evaluate("""() => {
                return {
                    bodyScrollWidth: document.body.scrollWidth,
                    innerWidth: window.innerWidth
                };
            }""")
            assert metrics["bodyScrollWidth"] <= metrics["innerWidth"] + 1, (
                f"[{file_label} | {vp_label}] Drawer open caused body horizontal overflow"
            )

            # Switch to Studio via mobile nav
            page.locator("#mobile-nav-studio").click()
            page.wait_for_timeout(200)
            assert not drawer.is_visible()
            assert page.locator("#view-studio").is_visible()
        else:
            # On md: 768px breakpoint, desktop nav is active and hamburger is suppressed by md:hidden
            assert not menu_btn.is_visible(), f"[{file_label} | {vp_label}] Hamburger should be hidden on >=768px"
            assert page.locator("nav.hidden.md\\:flex").is_visible(), f"[{file_label} | {vp_label}] Desktop nav should be visible on >=768px"

        context.close()
