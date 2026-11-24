import os
import shutil
import time
import sys
import traceback
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50"

def log(msg):
    print(msg, flush=True)

def run_verification():
    log("Starting Playwright verification for True Black UI...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            log("Navigating to http://127.0.0.1:8080/ ...")
            page.goto("http://127.0.0.1:8080/", wait_until="domcontentloaded")
            time.sleep(1)

            # 1. Verify computed styles
            bg_color = page.evaluate("getComputedStyle(document.body).backgroundColor")
            log(f"Body computed backgroundColor: {bg_color}")
            assert bg_color in ["rgb(0, 0, 0)", "#000000"], f"Expected rgb(0,0,0) but got {bg_color}"

            # 2. Verify no engine switch elements or unwanted text
            engine_pills = page.locator("#engineBadgePill").count()
            engine_switch_text = page.locator("text='Execution Engine Mode'").count()
            log(f"Engine badge pill count: {engine_pills}")
            log(f"Engine switch text count: {engine_switch_text}")
            assert engine_pills == 0, "Engine badge pill should not exist"
            assert engine_switch_text == 0, "Engine switch text should not exist"

            # 3. Screenshot Landing in True Black
            shot_dark = "web_app/screenshot_true_black.png"
            page.screenshot(path=shot_dark)
            log(f"Saved: {shot_dark}")

            # 4. Switch to Studio view
            page.click("#nav-studio")
            time.sleep(0.5)

            # Screenshot empty studio state
            shot_empty = "web_app/screenshot_studio_empty.png"
            page.screenshot(path=shot_empty)
            log(f"Saved: {shot_empty}")

            # 5. Load High-Availability Blueprint
            page.evaluate("window.loadSampleBlueprint()")
            time.sleep(1)
            log("Evaluated window.loadSampleBlueprint()")

            # Verify PRD rendered content in docContentContainer
            prd_text = page.locator("#docContentContainer").inner_text()
            log(f"PRD viewer preview: {prd_text[:100]}...")
            assert "High-Throughput Global Payments Gateway" in prd_text, "Sample PRD not rendered!"

            # Screenshot Studio with Sample Blueprint
            shot_sample = "web_app/screenshot_studio_sample.png"
            page.screenshot(path=shot_sample)
            log(f"Saved: {shot_sample}")

            # 6. Toggle to Vellum Light Mode
            page.click("#themeToggleBtn")
            time.sleep(0.5)

            # Verify Vellum background
            vellum_bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
            log(f"Vellum computed backgroundColor: {vellum_bg}")

            shot_vellum = "web_app/screenshot_vellum_sample.png"
            page.screenshot(path=shot_vellum)
            log(f"Saved: {shot_vellum}")

            browser.close()

        # Copy screenshots to artifact directory
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        for s in [shot_dark, shot_empty, shot_sample, shot_vellum]:
            dest = os.path.join(ARTIFACTS_DIR, os.path.basename(s))
            shutil.copy2(s, dest)
            log(f"Copied to artifact dir: {dest}")

        log("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")

    except Exception as e:
        log(f"ERROR DURING VERIFICATION: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
