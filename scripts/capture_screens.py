import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1366, "height": 768})
        await page.goto("http://127.0.0.1:8080/")
        await page.wait_for_timeout(1000)
        
        # 1. Landing page screenshot with sample audio button
        await page.screenshot(path=r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50\screenshot_sample_audio_button.png")
        print("Captured landing page with sample audio button")

        # 2. Click Council to open Council Chamber
        await page.click("button:has-text('COUNCIL')")
        await page.wait_for_timeout(600)
        await page.screenshot(path=r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50\screenshot_council_dossier_thoughts.png")
        print("Captured council modal with thoughts and artifact button")

        # 3. Click Architect seat
        await page.click("div:has-text('Architect')")
        await page.wait_for_timeout(300)
        await page.screenshot(path=r"C:\Users\ranan\.gemini\antigravity\brain\a18ad27a-24ab-4897-be58-2ae2f755ae50\screenshot_architect_seat_dossier.png")
        print("Captured architect seat dossier")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
