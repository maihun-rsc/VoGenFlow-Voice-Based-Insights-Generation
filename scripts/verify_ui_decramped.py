import os
import shutil
import time
import sys
import traceback
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50"

def log(msg):
    print(msg, flush=True)

def run_decramped_verification():
    log("Starting Playwright verification for de-cramped UI and immediate Council convening...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            log("Navigating to http://127.0.0.1:8080/ ...")
            page.goto("http://127.0.0.1:8080/", wait_until="domcontentloaded")
            time.sleep(1)

            # 1. Verify computed background color is true black
            bg_color = page.evaluate("getComputedStyle(document.body).backgroundColor")
            log(f"Body computed backgroundColor: {bg_color}")
            assert bg_color in ["rgb(0, 0, 0)", "#000000"], f"Expected rgb(0,0,0) but got {bg_color}"

            # 2. Verify landing console and prompt input exist
            landing_input = page.locator("#landingPromptInput")
            assert landing_input.count() > 0, "#landingPromptInput not found"
            log("Verified #landingPromptInput exists.")

            # 3. Screenshot Landing
            shot_landing = "web_app/screenshot_landing_decramped.png"
            page.screenshot(path=shot_landing)
            log(f"Saved: {shot_landing}")

            # 4. Test Immediate Council Convening from Landing!
            log("Testing immediate Council convening from prompt input...")
            landing_input.fill("High-Throughput Global Payments Gateway with Redis Redlock and PostgreSQL 16")
            
            # Click Convene Council & Generate button
            generate_btn = page.locator("button:has-text('CONVENE COUNCIL & GENERATE')").first
            generate_btn.click()
            log("Clicked 'CONVENE COUNCIL & GENERATE' button!")

            # Studio should be immediately visible
            time.sleep(1)
            is_studio_visible = page.locator("#view-studio").is_visible()
            log(f"Studio view visible after clicking generate: {is_studio_visible}")
            assert is_studio_visible, "Studio view should be visible immediately upon convening!"

            # Wait for council deliberation to complete (status changes DELIBERATING -> CONSENSUS)
            log("Waiting for Council deliberation to complete (status -> CONSENSUS)...")
            deliberation_done = False
            for i in range(40):
                time.sleep(0.5)
                status_text = page.locator("#pipelineStatusBadge").inner_text()
                if status_text == "CONSENSUS":
                    log(f"Council completed deliberation! Status: {status_text} (took {(i+1)*0.5:.1f}s)")
                    deliberation_done = True
                    break
            
            time.sleep(1)

            # Screenshot Studio
            shot_studio = "web_app/screenshot_studio_decramped.png"
            page.screenshot(path=shot_studio)
            log(f"Saved: {shot_studio}")

            # 5. Switch to Documents tab and inspect rendered specs
            page.click("#nav-specs")
            time.sleep(1)

            # Verify document content rendered
            doc_text = page.locator("#docContentContainer").inner_text()
            log(f"Doc viewer preview: {doc_text[:120]}...")
            assert "Product Requirements Document" in doc_text or "Executive Summary" in doc_text, f"Unexpected doc content: {doc_text[:60]}"

            shot_specs = "web_app/screenshot_specs_decramped.png"
            page.screenshot(path=shot_specs)
            log(f"Saved: {shot_specs}")

            # 6. Test RAG Ingestion Drawer toggle
            log("Testing RAG Ingestion Drawer toggle...")
            page.click("text=+ Ingest Custom Specs / Files")
            time.sleep(0.5)
            drawer_visible = page.locator("#ragIngestionDrawer").is_visible()
            log(f"RAG Drawer visible after click: {drawer_visible}")
            assert drawer_visible, "RAG Ingestion Drawer should expand on click"

            # 7. Test Vellum Light Mode with rendered documents
            page.click("#themeToggleBtn")
            time.sleep(0.5)
            shot_vellum = "web_app/screenshot_vellum_decramped.png"
            page.screenshot(path=shot_vellum)
            log(f"Saved: {shot_vellum}")

            browser.close()

        # Copy screenshots to artifact directory
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        for s in [shot_landing, shot_studio, shot_specs, shot_vellum]:
            dest = os.path.join(ARTIFACTS_DIR, os.path.basename(s))
            shutil.copy2(s, dest)
            log(f"Copied to artifact dir: {dest}")

        log("\nALL DE-CRAMPED UI & IMMEDIATE COUNCIL TESTS PASSED PERFECTLY!")

    except Exception as e:
        log(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_decramped_verification()
