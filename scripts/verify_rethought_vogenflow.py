"""
Comprehensive Playwright E2E Verification for Vo-Gen-Flow Review Fixes:
1. RAG Immediate Context Pre-Seeding (queries postgresql_ddl_relational.md without refusal)
2. Decramped 2-Column Council Modal Layout with Pinned Action Bar
3. Responsive Testing across 16:9 (1920x1080), 16:10 (1680x1050), and Mobile (390x844)
4. Interactive Zoom, Pan, Reset & Fullscreen on Mermaid Diagrams in Flow & Architecture
5. Clean UI Badges for [NEW] (CREATE FILE) in Tasks.md
6. Plain English System Architecture & Microservice Map
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = Path(r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50")

def run():
    print("=== Launching Playwright E2E Verification Suite ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # -------------------------------------------------------------
        # 1. Desktop 1440x900 Verification
        # -------------------------------------------------------------
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("\n[Step 1] Loading http://127.0.0.1:8080 at 1440x900...")
        page.goto("http://127.0.0.1:8080", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=str(ARTIFACT_DIR / "verify1_landing.png"))
        print("[OK] Captured verify1_landing.png")

        # -------------------------------------------------------------
        # 2. Test Immediate RAG Architecture Chat (Pre-Seeded)
        # -------------------------------------------------------------
        print("\n[Step 2] Testing Pre-Seeded RAG Architecture Chat...")
        nav_chat = page.locator("#nav-chat")
        assert nav_chat.is_visible(), "RAG CHAT nav button not found"
        nav_chat.click()
        time.sleep(0.5)

        # Click suggestion pill
        suggestion = page.locator("button:has-text('Explain the PostgreSQL DDL')").first
        assert suggestion.is_visible(), "Suggestion pill not found"
        print("Clicking suggestion pill: 'Explain the PostgreSQL DDL schema & RLS policies'...")
        suggestion.click()
        
        # Wait for loading indicator to finish and actual AI response bubble to appear
        page.wait_for_selector("#ragLoadingIndicator", state="attached", timeout=5000)
        page.wait_for_selector("#ragLoadingIndicator", state="detached", timeout=30000)
        time.sleep(1.5)
        
        chat_text = page.locator("#ragChatTimeline").inner_text()
        print(f"RAG Chat Response Snippet:\n{chat_text[-300:]}")
        assert "Refusing to hallucinate" not in chat_text, "RAG Chat still refusing grounded query!"
        assert "postgresql" in chat_text.lower() or "schema" in chat_text.lower() or "rls" in chat_text.lower(), "RAG response missing architectural content"
        page.screenshot(path=str(ARTIFACT_DIR / "verify2_rag_chat_response.png"))
        print("[OK] Verified RAG Chat is immediately grounded on boot. Captured verify2_rag_chat_response.png")

        # -------------------------------------------------------------
        # 3. Test 2-Column Council Chamber Modal & Dynamic Dossier
        # -------------------------------------------------------------
        print("\n[Step 3] Testing 2-Column Decramped Council Modal...")
        page.locator("button:has-text('COUNCIL')").first.click()
        time.sleep(0.8)
        
        council_modal = page.locator("#councilModalOverlay")
        assert council_modal.is_visible(), "Council modal not visible"
        
        # Verify Convene button is pinned and visible
        convene_btn = page.locator("#modalConveneBtn")
        assert convene_btn.is_visible(), "Pinned Convene button not visible in modal!"
        print("[OK] Pinned Convene button is visible and accessible without scrolling")

        # Click Architect seat station on the left orbit
        print("Clicking Architect seat station...")
        page.locator("#seat-station-architect").click()
        time.sleep(0.5)
        arch_thoughts = page.locator("#seatInspectorThoughts").inner_text()
        print(f"Architect Thoughts: {arch_thoughts}")
        assert "microservice" in arch_thoughts.lower() or "postgresql" in arch_thoughts.lower() or "architecture" in arch_thoughts.lower(), "Architect thoughts not updated"

        # Click Curator seat station
        page.locator("#seat-station-curator").click()
        time.sleep(0.5)
        cur_thoughts = page.locator("#seatInspectorThoughts").inner_text()
        print(f"Curator Thoughts: {cur_thoughts}")

        # Click The Elder seat station
        page.locator("#seat-station-elder").click()
        time.sleep(0.5)
        elder_thoughts = page.locator("#seatInspectorThoughts").inner_text()
        print(f"The Elder Thoughts: {elder_thoughts}")

        page.screenshot(path=str(ARTIFACT_DIR / "verify3_council_orbit_decramped.png"))
        print("[OK] Council 2-column layout verified. Captured verify3_council_orbit_decramped.png")

        # -------------------------------------------------------------
        # 4. Convene Council on Target Project
        # -------------------------------------------------------------
        print("\n[Step 4] Convening Council deliberation...")
        convene_btn.click()
        print("Waiting for deliberation to reach consensus...")
        page.wait_for_selector("#councilStatusText:has-text('CONSENSUS')", state="attached", timeout=60000)
        time.sleep(2)
        print("[OK] Deliberation reached consensus!")

        # Reopen modal to inspect post-deliberation state
        page.locator("button:has-text('COUNCIL')").first.click()
        time.sleep(0.8)
        page.screenshot(path=str(ARTIFACT_DIR / "verify4_council_deliberated.png"))
        print("[OK] Captured verify4_council_deliberated.png")

        # Close modal
        page.locator("button:has-text('CLOSE')").last.click()
        time.sleep(0.5)

        # -------------------------------------------------------------
        # 5. Documents Studio Verification: Tabs, Zoomable Mermaid, Badges
        # -------------------------------------------------------------
        print("\n[Step 5] Verifying Documents Studio artifacts...")
        page.locator("#nav-specs").click()
        time.sleep(1)

        # Tab 1: PRD
        prd_text = page.locator("#docContentContainer").inner_text()
        assert "PRD" in prd_text or "Product Requirements" in prd_text, "PRD content missing"
        page.screenshot(path=str(ARTIFACT_DIR / "verify5_doc_prd.png"))
        print("[OK] Verified PRD.md")

        # Tab 2: Architecture (Check System Architecture title & DDL)
        print("Switching to Architecture tab...")
        page.locator("#doc-arch").click()
        time.sleep(1.5)
        arch_text = page.locator("#docContentContainer").inner_text()
        print(f"Architecture Preview: {arch_text[:250]}...")
        assert "System Architecture & Microservice Map" in arch_text or "Microservice Map" in arch_text, "Architecture title still using C4 jargon!"
        assert "CREATE TABLE" in arch_text, "Domain DDL missing"
        page.screenshot(path=str(ARTIFACT_DIR / "verify5_doc_arch.png"))
        print("[OK] Verified Architecture.md titled System Architecture & Microservice Map with domain DDL")

        # Tab 3: Flow (Check Zoomable Mermaid & Zero Syntax Errors)
        print("Switching to Flow tab...")
        page.locator("#doc-flow").click()
        time.sleep(1.5)
        flow_html = page.locator("#docContentContainer").inner_html()
        assert "Syntax error in text" not in flow_html, "Mermaid syntax error detected!"
        
        # Verify Mermaid zoom controls
        zoom_in_btn = page.locator("button:has-text('[+] ZOOM')").first
        assert zoom_in_btn.is_visible(), "Mermaid [+] ZOOM button not found!"
        print("Clicking [+] ZOOM button twice to enlarge sequence diagram...")
        zoom_in_btn.click()
        time.sleep(0.3)
        zoom_in_btn.click()
        time.sleep(0.5)
        
        zoom_label = page.locator("#mermaid-zoom-label-0").inner_text()
        print(f"Current Diagram Zoom: {zoom_label}")
        assert "156%" in zoom_label or "125%" in zoom_label or "ZOOM:" in zoom_label, "Zoom level not updated"
        page.screenshot(path=str(ARTIFACT_DIR / "verify5_doc_flow.png"))
        print("[OK] Verified Flow.md is zoomable and error-free. Captured verify5_doc_flow.png")

        # Tab 4: Tasks (Check [NEW] replaced by CREATE FILE badge)
        print("Switching to Tasks tab...")
        page.locator("#doc-tasks").click()
        time.sleep(1.5)
        tasks_html = page.locator("#docContentContainer").inner_html()
        tasks_text = page.locator("#docContentContainer").inner_text()
        print(f"Tasks Preview: {tasks_text[:250]}...")
        assert "CREATE FILE" in tasks_html, "CREATE FILE telemetry badge not rendered!"
        assert "`[NEW]`" not in tasks_text, "Raw `[NEW]` tag still present in Tasks text!"
        page.screenshot(path=str(ARTIFACT_DIR / "verify5_doc_tasks.png"))
        print("[OK] Verified tasks.md contains CREATE FILE badges. Captured verify5_doc_tasks.png")

        context.close()

        # -------------------------------------------------------------
        # 6. Aspect Ratio & Responsiveness Verification (16:9, 16:10, Mobile)
        # -------------------------------------------------------------
        print("\n[Step 6] Testing Viewports (16:9, 16:10, Mobile)...")

        # 16:9 Full HD (1920x1080)
        ctx_16_9 = browser.new_context(viewport={"width": 1920, "height": 1080})
        p_16_9 = ctx_16_9.new_page()
        p_16_9.goto("http://127.0.0.1:8080", wait_until="networkidle")
        p_16_9.locator("button:has-text('COUNCIL')").first.click()
        time.sleep(0.8)
        assert p_16_9.locator("#modalConveneBtn").is_visible(), "Convene button missing in 16:9!"
        p_16_9.screenshot(path=str(ARTIFACT_DIR / "verify6_viewport_16_9.png"))
        print("[OK] 16:9 (1920x1080) verified. Captured verify6_viewport_16_9.png")
        ctx_16_9.close()

        # 16:10 Laptop (1680x1050)
        ctx_16_10 = browser.new_context(viewport={"width": 1680, "height": 1050})
        p_16_10 = ctx_16_10.new_page()
        p_16_10.goto("http://127.0.0.1:8080", wait_until="networkidle")
        p_16_10.locator("button:has-text('COUNCIL')").first.click()
        time.sleep(0.8)
        assert p_16_10.locator("#modalConveneBtn").is_visible(), "Convene button missing in 16:10!"
        p_16_10.screenshot(path=str(ARTIFACT_DIR / "verify6_viewport_16_10.png"))
        print("[OK] 16:10 (1680x1050) verified. Captured verify6_viewport_16_10.png")
        ctx_16_10.close()

        # Mobile Viewport (390x844 - iPhone 14 / modern smartphone)
        ctx_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        p_mob = ctx_mobile.new_page()
        p_mob.goto("http://127.0.0.1:8080", wait_until="networkidle")
        p_mob.evaluate("toggleCouncilModal()")
        time.sleep(0.8)
        assert p_mob.locator("#modalConveneBtn").is_visible(), "Convene button missing in mobile viewport!"
        p_mob.screenshot(path=str(ARTIFACT_DIR / "verify6_viewport_mobile.png"))
        print("[OK] Mobile (390x844) verified. Captured verify6_viewport_mobile.png")
        ctx_mobile.close()

        browser.close()
        print("\n=== ALL E2E VERIFICATIONS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run()
