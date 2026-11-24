from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    for h in [900, 800, 768, 720, 650, 600]:
        page = browser.new_page(viewport={"width": 1280, "height": h})
        page.goto("http://127.0.0.1:8080/")
        
        # 1. Check Global Header Convene Button (Outside Modal)
        global_btn = page.locator("header button:has-text('CONVENE')")
        g_box = global_btn.bounding_box()
        g_vis = (g_box["y"] + g_box["height"]) <= h if g_box else False
        
        # 2. Open Modal and check both Top and Bottom Convene Buttons
        page.evaluate("toggleCouncilModal()")
        
        top_btn = page.locator("#councilModalOverlay button:has-text('CONVENE')").first
        t_box = top_btn.bounding_box()
        t_vis = (t_box["y"] + t_box["height"]) <= h and t_box["y"] >= 0 if t_box else False
        
        bot_btn = page.locator("#councilModalOverlay button:has-text('CONVENE COUNCIL & GENERATE')")
        b_box = bot_btn.bounding_box()
        b_vis = (b_box["y"] + b_box["height"]) <= h and b_box["y"] >= 0 if b_box else False
        
        print(f"Viewport height {h}px: Global Header Convene visible={g_vis} (y={g_box['y']:.1f}) | Modal Top Convene visible={t_vis} (y={t_box['y']:.1f}) | Modal Bottom Convene visible={b_vis} (y={b_box['y']:.1f})")
    browser.close()
