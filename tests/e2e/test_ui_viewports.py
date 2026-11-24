"""
tests/e2e/test_ui_viewports.py
Tier 4: Live Headless E2E Simulation Test Suite via Playwright.

Verifies:
1. Static DOM Structure & Monolith Luxury design tokens on web_app/index.html and frontend_demo.html
2. Responsive layout rendering across 4 standard screen dimensions:
   - Desktop 1080p (1920x1080)
   - Laptop (1440x900)
   - Mobile iPhone X (375x812)
   - Mobile iPhone 11 (414x896)
3. Zero horizontal body overflow (scrollWidth <= clientWidth) across all 4 views and modal
4. Mobile navigation drawer (#mobileNavDrawer) toggle, view switching, and auto-close
5. Desktop navigation visibility and mobile hamburger suppression
6. Dynamic theme switching between Onyx True Black and Monolith Vellum Light
7. 100% Structural and code parity between web_app/index.html and frontend_demo.html
"""

import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
INDEX_HTML = ROOT_DIR / "web_app" / "index.html"
DEMO_HTML = ROOT_DIR / "frontend_demo.html"

TARGET_FILES = [
    ("web_app/index.html", INDEX_HTML.as_uri()),
    ("frontend_demo.html", DEMO_HTML.as_uri()),
]

VIEWPORTS = [
    ("Desktop 1080p", 1920, 1080),
    ("Laptop", 1440, 900),
    ("Mobile iPhone X", 375, 812),
    ("Mobile iPhone 11", 414, 896),
]

VIEWS = ["landing", "studio", "specs", "chat"]


@pytest.fixture(scope="module")
def browser_instance():
    """Launch headless Chromium browser instance for Tier 4 E2E simulation."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.mark.e2e
class TestDOMStructureAndParity:
    """Verify HTML DOM integrity, luxury tokens, and file parity."""

    def test_file_existence(self):
        """Verify both web_app/index.html and frontend_demo.html exist."""
        assert INDEX_HTML.exists(), "web_app/index.html does not exist"
        assert DEMO_HTML.exists(), "frontend_demo.html does not exist"

    def test_file_content_parity(self):
        """Verify byte-for-byte parity between web_app/index.html and frontend_demo.html."""
        index_content = INDEX_HTML.read_text(encoding="utf-8")
        demo_content = DEMO_HTML.read_text(encoding="utf-8")
        assert index_content == demo_content, "web_app/index.html and frontend_demo.html have drifted out of sync"

    def test_luxury_theme_tokens_and_typography(self):
        """Verify Monolith luxury fonts, gold accents, and theme styles in DOM."""
        content = INDEX_HTML.read_text(encoding="utf-8")
        # Fonts
        assert "Instrument+Serif" in content, "Missing Instrument Serif luxury font"
        assert "Plus+Jakarta+Sans" in content, "Missing Plus Jakarta Sans font"
        assert "JetBrains+Mono" in content, "Missing JetBrains Mono font"

        # Theme color variables
        assert "--accent-gold" in content, "Missing --accent-gold token"
        assert "theme-vellum" in content, "Missing theme-vellum light theme class definition"
        assert "#000000" in content, "Missing Onyx True Black base background"

        # Key interactive elements
        assert 'id="mobileMenuToggleBtn"' in content, "Missing mobile hamburger button"
        assert 'id="mobileNavDrawer"' in content, "Missing mobile navigation drawer"
        assert 'id="councilModalOverlay"' in content, "Missing council modal overlay"
        assert 'id="heroMicBtn"' in content, "Missing hero mic dictate button"


@pytest.mark.e2e
class TestResponsiveViewportsAndOverflow:
    """Verify viewport rendering, layout stability, and zero horizontal overflow."""

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    @pytest.mark.parametrize("vp_name,width,height", VIEWPORTS)
    def test_viewports_zero_horizontal_overflow(self, browser_instance, file_label, file_url, vp_name, width, height):
        """Assert scrollWidth <= clientWidth across all 4 views on standard viewports."""
        context = browser_instance.new_context(viewport={"width": width, "height": height})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

        page.goto(file_url, wait_until="domcontentloaded")
        page.wait_for_timeout(300)

        # Check each of the 4 main application views
        for view_name in VIEWS:
            page.evaluate(f"switchView('{view_name}')")
            page.wait_for_timeout(150)

            scroll_w = page.evaluate("document.body.scrollWidth")
            client_w = page.evaluate("document.documentElement.clientWidth")
            assert scroll_w <= client_w, (
                f"[{file_label} | {vp_name}] View '{view_name}' horizontal overflow detected: "
                f"scrollWidth={scroll_w} > clientWidth={client_w}"
            )

        # Check council modal open state
        page.evaluate("toggleCouncilModal()")
        page.wait_for_timeout(150)
        modal_scroll_w = page.evaluate("document.body.scrollWidth")
        modal_client_w = page.evaluate("document.documentElement.clientWidth")
        assert modal_scroll_w <= modal_client_w, (
            f"[{file_label} | {vp_name}] Council modal caused horizontal overflow: "
            f"scrollWidth={modal_scroll_w} > clientWidth={modal_client_w}"
        )
        page.evaluate("toggleCouncilModal()")

        # Verify no catastrophic JavaScript runtime errors
        critical_errors = [e for e in console_errors if "ERR_CONNECTION_REFUSED" not in e]
        assert len(critical_errors) == 0, f"[{file_label} | {vp_name}] Console errors: {critical_errors}"

        context.close()


@pytest.mark.e2e
class TestMobileNavigationInteractions:
    """Verify mobile drawer toggle, view switching, and navigation semantics."""

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    def test_mobile_hamburger_drawer_lifecycle(self, browser_instance, file_label, file_url):
        """Verify hamburger toggle opens drawer, navigation clicks switch views and auto-close drawer."""
        context = browser_instance.new_context(viewport={"width": 375, "height": 812})
        page = context.new_page()
        page.goto(file_url, wait_until="domcontentloaded")
        page.wait_for_timeout(300)

        # 1. Verify hamburger button is visible, drawer is closed
        menu_btn = page.locator("#mobileMenuToggleBtn")
        assert menu_btn.is_visible(), "Hamburger button should be visible on 375px mobile"

        drawer = page.locator("#mobileNavDrawer")
        assert not drawer.is_visible(), "Mobile nav drawer should be hidden initially"

        # 2. Click hamburger button to open drawer
        menu_btn.click()
        page.wait_for_timeout(200)
        assert drawer.is_visible(), "Mobile nav drawer should open after clicking hamburger"

        # 3. Check icon transition
        assert page.locator("#closeMenuIcon").is_visible(), "Close menu icon should be visible"
        assert not page.locator("#hamburgerIcon").is_visible(), "Hamburger icon should be hidden"

        # 4. Navigate to Studio
        page.locator("#mobile-nav-studio").click()
        page.wait_for_timeout(200)
        assert not drawer.is_visible(), "Drawer should auto-close after view navigation"
        assert page.locator("#view-studio").is_visible(), "Studio view should now be active"

        # 5. Open drawer again and navigate to Specs
        menu_btn.click()
        page.wait_for_timeout(200)
        page.locator("#mobile-nav-specs").click()
        page.wait_for_timeout(200)
        assert not drawer.is_visible(), "Drawer should auto-close"
        assert page.locator("#view-specs").is_visible(), "Specs view should now be active"

        # 6. Open drawer again and navigate to Chat
        menu_btn.click()
        page.wait_for_timeout(200)
        page.locator("#mobile-nav-chat").click()
        page.wait_for_timeout(200)
        assert not drawer.is_visible(), "Drawer should auto-close"
        assert page.locator("#view-chat").is_visible(), "Chat view should now be active"

        context.close()

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    def test_desktop_nav_visibility_and_hamburger_hidden(self, browser_instance, file_label, file_url):
        """Verify desktop header renders top navigation and hides hamburger button on 1920x1080."""
        context = browser_instance.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page.goto(file_url, wait_until="domcontentloaded")
        page.wait_for_timeout(300)

        # Hamburger must be hidden on desktop
        assert not page.locator("#mobileMenuToggleBtn").is_visible(), "Hamburger must be hidden on 1080p"

        # Desktop nav bar must be visible
        assert page.locator("nav.md\\:flex").is_visible(), "Desktop nav bar must be visible on 1080p"

        # Switch views on desktop
        for v in VIEWS:
            page.locator(f"#nav-{v}").click()
            page.wait_for_timeout(150)
            assert page.locator(f"#view-{v}").is_visible(), f"View '{v}' should be visible after desktop click"

        context.close()

    @pytest.mark.parametrize("file_label,file_url", TARGET_FILES)
    def test_theme_toggle_flow(self, browser_instance, file_label, file_url):
        """Verify theme toggle between Onyx True Black and Monolith Vellum Light."""
        context = browser_instance.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(file_url, wait_until="domcontentloaded")
        page.wait_for_timeout(300)

        # Initially Onyx (dark)
        initial_class = page.evaluate("document.body.className")
        assert "theme-vellum" not in initial_class

        # Toggle to Vellum Light
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(200)
        vellum_class = page.evaluate("document.body.className")
        assert "theme-vellum" in vellum_class, "Body should have theme-vellum class after toggle"

        # Toggle back to Onyx Dark
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(200)
        reverted_class = page.evaluate("document.body.className")
        assert "theme-vellum" not in reverted_class, "Body should revert to Onyx without theme-vellum class"

        context.close()
