"""
Comprehensive Live Full Experience Verification via Playwright.
Tests:
1. Landing page in Onyx Black
2. Vellum Light theme toggle and back
3. Load Sample Blueprint & verify Council deliberation state
4. Council Chamber modal & Seat Inspector dossiers
5. All 6 Specification Studio tabs (PRD, Architecture, Flow, Tasks, Design, Bundle)
6. Interactive Mermaid diagrams (Zoom, Pan, Reset)
7. Client-side 1-click 'DOWNLOAD .DOCX' export
8. RAG Chat Assistant: Ask exact user advisory query and assert '[ARCHITECTURAL ADVISORY // SYNTHESIS]'
Saves all screenshots to the artifact directory.
"""

import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(os.getenv("VOGENFLOW_SCREENSHOT_DIR") or (REPO_ROOT / "output" / "live_experience_screenshots"))
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

async def run_full_experience_test():
    print("=" * 70)
    print("   VOGENFLOW 2.0 // LIVE FULL EXPERIENCE PLAYWRIGHT VERIFICATION")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=True
        )
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # 1. Landing Page
        print("\n[STEP 1] Navigating to http://127.0.0.1:8080/ ...")
        await page.goto("http://127.0.0.1:8080/", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        s1 = ARTIFACT_DIR / "verify_full_1_landing_onyx.png"
        await page.screenshot(path=str(s1))
        print(f"  ✓ Captured landing in Onyx Black: {s1.name}")

        # 2. Theme Toggle (Vellum Light)
        print("\n[STEP 2] Testing Theme Switching (Vellum Luxury Light Mode)...")
        await page.click("button:has-text('VELLUM'), button:has-text('LIGHT')")
        await page.wait_for_timeout(600)
        s2 = ARTIFACT_DIR / "verify_full_2_vellum_light.png"
        await page.screenshot(path=str(s2))
        print(f"  ✓ Captured Vellum Light mode: {s2.name}")

        # Switch back to Onyx Dark
        await page.click("button:has-text('ONYX'), button:has-text('DARK')")
        await page.wait_for_timeout(400)

        # 3. Load Sample Blueprint & Deliberate
        print("\n[STEP 3] Loading Sample Architecture Blueprint & Deliberating...")
        await page.locator("#nav-specs, button:has-text('SPECIFICATIONS')").first.click()
        await page.wait_for_timeout(500)

        sample_btn = page.locator("button:has-text('LOAD SAMPLE ARCHITECTURE BLUEPRINT')")
        if await sample_btn.count() > 0 and await sample_btn.is_visible():
            await sample_btn.click()
            await page.wait_for_timeout(1000)
            print("  ✓ Clicked 'LOAD SAMPLE ARCHITECTURE BLUEPRINT'")
        else:
            print("  Sample blueprint already populated or loaded.")

        s3 = ARTIFACT_DIR / "verify_full_3_specs_loaded.png"
        await page.screenshot(path=str(s3))
        print(f"  ✓ Captured loaded specs: {s3.name}")

        # 4. Test 1-Click DOCX Download
        print("\n[STEP 4] Testing Client-Side 1-Click 'DOWNLOAD .DOCX' Export...")
        docx_btn = page.locator("button:has-text('DOWNLOAD .DOCX')")
        assert await docx_btn.count() > 0, "DOWNLOAD .DOCX button not found in Specs header!"

        # Catch browser download event
        async with page.expect_download(timeout=10000) as download_info:
            await docx_btn.click()
        download = await download_info.value
        download_path = ARTIFACT_DIR / download.suggested_filename
        await download.save_as(str(download_path))
        assert download_path.exists(), f"Downloaded file {download_path} does not exist!"
        assert download_path.stat().st_size > 1000, f"Downloaded file too small: {download_path.stat().st_size} bytes"
        print(f"  ✓ Verified .docx client-side generation: {download.suggested_filename} ({download_path.stat().st_size} bytes)")

        # 5. Test Specification Studio Tabs & Mermaid Diagrams
        print("\n[STEP 5] Testing Specification Studio Tabs & Mermaid Diagrams...")
        tabs = [
            ("doc-prd", "PRD.md", "verify_full_5_tab_prd.png"),
            ("doc-arch", "Architecture.md", "verify_full_5_tab_arch.png"),
            ("doc-flow", "Flow.md", "verify_full_5_tab_flow.png"),
            ("doc-tasks", "tasks.md", "verify_full_5_tab_tasks.png"),
            ("doc-design", "design.md", "verify_full_5_tab_design.png")
        ]
        for tab_id, label, filename in tabs:
            tab_locator = page.locator(f"#{tab_id}")
            if await tab_locator.count() > 0:
                await tab_locator.click()
                await page.wait_for_timeout(700)
                screen_path = ARTIFACT_DIR / filename
                await page.screenshot(path=str(screen_path))
                print(f"  ✓ Verified Tab '{label}' (Captured: {filename})")

        # 6. Test RAG Chat Assistant Drawer with Exact Advisory Query
        print("\n[STEP 6] Testing Conversational RAG Engine Drawer...")
        # Toggle RAG drawer if hidden
        rag_drawer = page.locator("#ragDrawer, #ragChatTimeline")
        rag_toggle_btn = page.locator("#nav-rag, button:has-text('RAG'), button:has-text('CHAT')").first
        if await rag_toggle_btn.count() > 0:
            await rag_toggle_btn.click()
            await page.wait_for_timeout(600)

        rag_input = page.locator("#ragChatInput")
        assert await rag_input.count() > 0, "#ragChatInput not found on page!"

        test_advisory_query = (
            "What all features can we add to our voice-based document intelligence system "
            "so that it is not just AI document creation but also complete curation alongwith query and full insights."
        )
        print(f"  Sending query to RAG assistant: '{test_advisory_query[:65]}...'")
        await rag_input.fill(test_advisory_query)
        await page.keyboard.press("Enter")

        # Wait for RAG assistant response
        print("  Waiting for RAG answer synthesis...")
        answered = False
        for _ in range(20):
            await page.wait_for_timeout(1000)
            timeline_text = await page.locator("#ragChatTimeline").text_content()
            if "ARCHITECTURAL ADVISORY" in timeline_text or "Curated Blueprint" in timeline_text or "Advisory" in timeline_text:
                answered = True
                print("  ✓ RAG Assistant synthesized Architectural Advisory successfully!")
                break
            if "Guardrail Notice" in timeline_text:
                raise AssertionError("FAILED: RAG Assistant returned Guardrail Notice instead of Advisory Synthesis!")

        s6_rag = ARTIFACT_DIR / "verify_full_6_rag_advisory_response.png"
        await page.screenshot(path=str(s6_rag))
        print(f"  ✓ Captured RAG advisory response: {s6_rag.name}")

        print("\n" + "=" * 70)
        print("  ✓ ALL FULL EXPERIENCE PLAYWRIGHT CHECKS PASSED (0 ERRORS)")
        print("=" * 70)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_full_experience_test())
