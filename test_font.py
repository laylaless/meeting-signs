import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=EXE)
        page = await browser.new_page()
        await page.goto(URL)
        # 等字体加载完成
        await page.evaluate("document.fonts.load('64pt STXinwei')")
        await page.wait_for_timeout(800)

        r = await page.evaluate("""async () => {
            await document.fonts.ready;
            const ok = document.fonts.check("64pt STXinwei");
            const c = document.createElement('canvas').getContext('2d');
            c.font = "64pt STXinwei";      const m1 = c.measureText('张三丰');
            c.font = "64pt 'Songti SC'";    const m3 = c.measureText('张三丰');
            // 汉字 advance 均为 1em 无法区分字体，用垂直排版度量（不同字体的 ascent/descent 不同）
            const box1 = [m1.fontBoundingBoxAscent, m1.fontBoundingBoxDescent];
            const box3 = [m3.fontBoundingBoxAscent, m3.fontBoundingBoxDescent];
            return {ok, box1, box3, w1: m1.width,
                    loaded: [...document.fonts].map(f=>f.family+':'+f.status)};
        }""")
        print(r)
        assert r["ok"], "STXinwei 未注册"
        same = abs(r["box1"][0]-r["box3"][0])<0.5 and abs(r["box1"][1]-r["box3"][1])<0.5
        print(f"STXinwei bbox={r['box1']} vs Songti bbox={r['box3']} → {'相同(可疑)' if same else '不同(字体独立生效)'}")

        # 台签页实际渲染检查
        await page.get_by_placeholder("张三｜党工委书记").fill("张三\n李四")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="② 台签打印").click()
        used = await page.evaluate("""() => {
            const el = document.querySelector('#sign-preview .sign-name');
            const cs = getComputedStyle(el);
            return {family: cs.fontFamily.slice(0,40), size: cs.fontSize};
        }""")
        print("预览 sign-name 计算样式:", used)
        await page.screenshot(path="_preview_check.png", full_page=False)
        await page.evaluate("localStorage.clear()")
        await browser.close()
        print("PASS")

asyncio.run(main())
