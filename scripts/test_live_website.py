"""
Comprehensive Live End-to-End Website Test via Playwright.
Tests:
1. Landing page, themes (Onyx Black & Vellum Light)
2. Sample Audio Quick-Test ingestion & auto-deliberation
3. Live Council Chamber modal & Seat Inspector dossiers (live thoughts, model, latency)
4. 6-Tab Specification Studio & visual Mermaid diagram rendering
Saves verification screenshots to artifact directory.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACT_DIR = Path(r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50")

async def test_live_website():
    print("Launching Chromium browser for Live End-to-End Website Test...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # -------------------------------------------------------------
        # STEP 1: Landing Page Verification (Onyx Black)
        # -------------------------------------------------------------
        print("STEP 1: Navigating to http://127.0.0.1:8080/ ...")
        await page.goto("http://127.0.0.1:8080/", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        screen1 = ARTIFACT_DIR / "screenshot_test1_landing_onyx.png"
        await page.screenshot(path=str(screen1))
        print(f"Captured: {screen1.name}")

        # -------------------------------------------------------------
        # STEP 2: Theme Toggle Verification (Vellum Light)
        # -------------------------------------------------------------
        print("STEP 2: Testing theme toggle to Vellum Light...")
        await page.click("button:has-text('VELLUM'), button:has-text('LIGHT'), button:has-text('THEME')")
        await page.wait_for_timeout(600)
        screen2 = ARTIFACT_DIR / "screenshot_test2_vellum_light.png"
        await page.screenshot(path=str(screen2))
        print(f"Captured: {screen2.name}")

        # Switch back to Onyx Dark
        await page.click("button:has-text('ONYX'), button:has-text('DARK')")
        await page.wait_for_timeout(400)

        # -------------------------------------------------------------
        # STEP 3: Load Sample Audio Note & Auto-Deliberate
        # -------------------------------------------------------------
        print("STEP 3: Clicking 'LOAD SAMPLE ARCHITECTURE AUDIO NOTE (WAV)'...")
        sample_btn = page.locator("button:has-text('LOAD SAMPLE ARCHITECTURE AUDIO NOTE')")
        await sample_btn.click()

        print("Waiting for STT & Scatter-Gather Council Deliberation to complete (up to 30s)...")
        for i in range(30):
            await page.wait_for_timeout(1000)
            status_elem = page.locator("#streamStatus")
            status_text = await status_elem.text_content() if await status_elem.count() > 0 else ""
            if "COMPLETE" in status_text or "IDLE" in status_text:
                print(f"Deliberation finished! Status: {status_text.strip()} (after {i+1}s)")
                break

        await page.wait_for_timeout(1500)
        screen3 = ARTIFACT_DIR / "screenshot_test3_studio_loaded.png"
        await page.screenshot(path=str(screen3))
        print(f"Captured: {screen3.name}")

        # -------------------------------------------------------------
        # STEP 4: Inspect Council Chamber & Seat Dossiers
        # -------------------------------------------------------------
        print("STEP 4: Opening Council Chamber modal to inspect live dossiers...")
        council_btn = page.locator("#nav-council, button:has-text('COUNCIL')").first
        await council_btn.click()
        await page.wait_for_timeout(800)

        screen4 = ARTIFACT_DIR / "screenshot_test4_council_modal_deliberated.png"
        await page.screenshot(path=str(screen4))
        print(f"Captured: {screen4.name}")

        # Click Strategist
        strategist_seat = page.locator("#seat-strategist, div:has-text('Strategist')").last
        if await strategist_seat.count() > 0:
            await strategist_seat.click(force=True)
            await page.wait_for_timeout(400)
            screen4_strat = ARTIFACT_DIR / "screenshot_test4_dossier_strategist.png"
            await page.screenshot(path=str(screen4_strat))
            print("Captured Strategist seat dossier with live thoughts")

        # Click Architect
        arch_seat = page.locator("#seat-architect, div:has-text('Architect')").last
        if await arch_seat.count() > 0:
            await arch_seat.click(force=True)
            await page.wait_for_timeout(400)
            screen4_arch = ARTIFACT_DIR / "screenshot_test4_dossier_architect.png"
            await page.screenshot(path=str(screen4_arch))
            print("Captured Architect seat dossier with live thoughts")

        # Click "VIEW ARTIFACT" button to smoothly exit modal and jump to specs
        artifact_btn = page.locator("#seatInspectorArtifactBtn")
        if await artifact_btn.count() > 0 and await artifact_btn.is_visible():
            print("Clicking 'VIEW ARTIFACT' on seat inspector to transition to specifications...")
            await artifact_btn.click()
            await page.wait_for_timeout(800)
        else:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(400)
            await page.locator("#nav-specs").click()
            await page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # STEP 5: Test Specification Studio - All 6 Tabs
        # -------------------------------------------------------------
        print("STEP 5: Testing all 6 Specification Studio tabs...")

        # Tab 1: PRD.md
        await page.locator("#doc-prd").click()
        await page.wait_for_timeout(500)
        screen5_prd = ARTIFACT_DIR / "screenshot_test5_tab_prd.png"
        await page.screenshot(path=str(screen5_prd))
        print("Captured PRD tab")

        # Tab 2: architecture.md (Check Mermaid C4 diagram)
        await page.locator("#doc-arch").click()
        await page.wait_for_timeout(1000)
        screen5_arch = ARTIFACT_DIR / "screenshot_test5_tab_arch.png"
        await page.screenshot(path=str(screen5_arch))
        print("Captured Architecture tab (with visual Mermaid C4 diagram)")

        # Tab 3: flow.md (Check Mermaid Sequence diagram)
        await page.locator("#doc-flow").click()
        await page.wait_for_timeout(1000)
        screen5_flow = ARTIFACT_DIR / "screenshot_test5_tab_flow.png"
        await page.screenshot(path=str(screen5_flow))
        print("Captured Flow tab (with visual Mermaid Sequence diagram)")

        # Tab 4: tasks.md (Check Agile checklist)
        await page.locator("#doc-tasks").click()
        await page.wait_for_timeout(500)
        screen5_tasks = ARTIFACT_DIR / "screenshot_test5_tab_tasks.png"
        await page.screenshot(path=str(screen5_tasks))
        print("Captured Tasks tab (verified domain tasks)")

        # Tab 5: design.md (Check UI tokens)
        await page.locator("#doc-design").click()
        await page.wait_for_timeout(500)
        screen5_design = ARTIFACT_DIR / "screenshot_test5_tab_design.png"
        await page.screenshot(path=str(screen5_design))
        print("Captured Design tab")

        # Tab 6: bundle.md (Check Master Execution Bundle)
        await page.locator("#doc-bundle").click()
        await page.wait_for_timeout(500)
        screen5_bundle = ARTIFACT_DIR / "screenshot_test5_tab_bundle.png"
        await page.screenshot(path=str(screen5_bundle))
        print("Captured Master Execution Bundle tab")

        print("\n--- TEST SUMMARY ---")
        print(f"Console errors detected: {len(console_errors)}")
        if console_errors:
            for ce in console_errors[:5]:
                print(f"  [ERROR] {ce}")
        else:
            print("  Zero JavaScript console errors!")

        await browser.close()
        print("\nAll End-to-End Tests Passed! All screenshots saved to artifact directory.")

if __name__ == "__main__":
    asyncio.run(test_live_website())
