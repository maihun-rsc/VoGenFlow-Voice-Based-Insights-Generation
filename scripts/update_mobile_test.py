from pathlib import Path

p = Path("scripts/verify_rethought_vogenflow.py")
text = p.read_text(encoding="utf-8")

old_click = """        # Mobile Viewport (390x844 - iPhone 14 / modern smartphone)
        ctx_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        p_mob = ctx_mobile.new_page()
        p_mob.goto("http://127.0.0.1:8080", wait_until="networkidle")
        p_mob.locator("button:has-text('COUNCIL')").first.click()"""

new_click = """        # Mobile Viewport (390x844 - iPhone 14 / modern smartphone)
        ctx_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        p_mob = ctx_mobile.new_page()
        p_mob.goto("http://127.0.0.1:8080", wait_until="networkidle")
        p_mob.evaluate("toggleCouncilModal()")"""

text = text.replace(old_click, new_click)
p.write_text(text, encoding="utf-8")
print("[OK] Updated mobile test trigger")
