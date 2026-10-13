"""Headless QA: screenshot a page at 390x664 and 1440x900, report horizontal overflow,
tap a citation, switch tabs. Usage: python3 scripts/shoot.py <url> <outdir>"""
import sys
from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    for eng, w, h in (("webkit", 390, 664), ("chromium", 1440, 900)):
        b = getattr(p, eng).launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if w < 500 else 1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(500)
        tabs = pg.locator("#tabs button")
        for i in range(tabs.count()):
            tabs.nth(i).click()
            pg.wait_for_timeout(200)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            first = pg.locator("button.c[data-q]").first
            if first.count():
                first.click()
            pg.screenshot(path=f"{out}/{w}_{i}.png", full_page=False)
            if i == 0:
                pg.screenshot(path=f"{out}/{w}_{i}_full.png", full_page=True)
            small = pg.evaluate("""[...document.querySelectorAll('button')].filter(b=>b.offsetParent&&b.getBoundingClientRect().height<24).length""")
            print(f"{eng} {w}x{h} tab{i}: scrollWidth={sw} (overflow={sw > w}) small_buttons={small} errors={errs}")
        b.close()
