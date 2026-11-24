import os
import shutil
import time
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50"

def log(msg):
    print(msg, flush=True)

def run():
    log("Starting Playwright verification for Spacious Council Chamber Modal...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        log("Navigating to http://127.0.0.1:8080/ ...")
        page.goto("http://127.0.0.1:8080/", wait_until="domcontentloaded")
        time.sleep(1)

        # 1. Open the Council Modal
        log("Opening Council Chamber modal...")
        page.evaluate("toggleCouncilModal()")
        time.sleep(0.5)

        is_modal_visible = page.locator("#councilModalOverlay").is_visible()
        log(f"Council modal visible: {is_modal_visible}")
        assert is_modal_visible, "Council modal should be visible after toggle!"

        # 2. Verify all 5 seat stations exist and measure bounding boxes to guarantee NO overlap
        seats = [
            ("Strategist", "STR"),
            ("Architect", "ARC"),
            ("Curator", "CUR"),
            ("Linguist", "LIN"),
            ("The Elder", "ELD")
        ]
        
        boxes = {}
        for name, code in seats:
            locator = page.locator(f".seat-station:has-text('{code}')").first
            assert locator.count() > 0, f"Seat station {code} not found"
            box = locator.bounding_box()
            boxes[code] = box
            log(f"Seat {code} ({name}) bounding box: x={box['x']:.1f}, y={box['y']:.1f}, w={box['width']:.1f}, h={box['height']:.1f}")

        # Check pairwise bounding boxes for overlap
        seat_codes = [s[1] for s in seats]
        for i in range(len(seat_codes)):
            for j in range(i + 1, len(seat_codes)):
                c1, c2 = seat_codes[i], seat_codes[j]
                b1, b2 = boxes[c1], boxes[c2]
                overlap_x = max(0, min(b1['x'] + b1['width'], b2['x'] + b2['width']) - max(b1['x'], b2['x']))
                overlap_y = max(0, min(b1['y'] + b1['height'], b2['y'] + b2['height']) - max(b1['y'], b2['y']))
                assert overlap_x == 0 or overlap_y == 0, f"Collision detected between {c1} and {c2}! Overlap: {overlap_x}x{overlap_y}"
        log("SUCCESS: All 5 seats are verified to have ZERO spatial collision or overlap!")

        # 3. Test clicking Architect seat
        log("Clicking Architect seat (ARC)...")
        page.click(".seat-station:has-text('ARC')")
        time.sleep(0.5)
        title_text = page.locator("#seatInspectorTitle").inner_text()
        log(f"Dossier Title after clicking ARC: {title_text}")
        assert "Architect" in title_text, f"Expected Architect in title, got: {title_text}"

        # 4. Take screenshot of Spacious Council Chamber in Onyx True Black
        shot_dark = "web_app/screenshot_council_chamber_spacious.png"
        page.screenshot(path=shot_dark)
        log(f"Saved: {shot_dark}")

        # 5. Switch to Monolith Vellum and take screenshot
        page.evaluate("toggleCouncilModal()") # close
        time.sleep(0.3)
        page.click("#themeToggleBtn") # switch to vellum
        time.sleep(0.5)
        page.evaluate("toggleCouncilModal()") # open
        time.sleep(0.5)

        # Click The Elder seat in Vellum mode
        log("Clicking The Elder seat (ELD) in Vellum mode...")
        page.click(".seat-station:has-text('ELD')")
        time.sleep(0.5)
        title_text_eld = page.locator("#seatInspectorTitle").inner_text()
        log(f"Dossier Title after clicking ELD: {title_text_eld}")
        assert "The Elder" in title_text_eld

        shot_vellum = "web_app/screenshot_council_chamber_vellum.png"
        page.screenshot(path=shot_vellum)
        log(f"Saved: {shot_vellum}")

        # Copy to artifacts directory
        for s in [shot_dark, shot_vellum]:
            dest = os.path.join(ARTIFACTS_DIR, os.path.basename(s))
            shutil.copy2(s, dest)
            log(f"Copied to artifact dir: {dest}")

        browser.close()
        log("\nALL COUNCIL CHAMBER TESTS & GEOMETRY VERIFICATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    run()
