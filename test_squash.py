import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=EXE)
        page = await browser.new_page()
        await page.goto(URL)
        await page.evaluate("window.print=()=>{}")   # mock 打印
        await page.wait_for_function("document.fonts.status==='loaded'")

        # 1. 短名（3字）：不压缩、单行、无 scaleX
        await page.get_by_placeholder("张三｜党工委书记").fill("张三｜党工委书记")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="② 台签打印").click()
        nm = page.locator("#sign-preview .sign-name").first
        style = await nm.get_attribute("style") or ""
        h_px = await nm.evaluate("el=>el.offsetHeight")
        print(f"3字名 style含scaleX: {'scaleX' in style} | 高: {h_px}px(单行≈128)")
        assert "scaleX" not in style
        assert h_px < 320   # 155pt 单行约 207px，换行会翻倍

        # 2. 长名（6字）：自然宽约 203mm > 186mm 可用宽 → 触发 scaleX，高度不变
        await page.get_by_role("button", name="① 名单").click()
        await page.get_by_placeholder("张三｜党工委书记").fill("欧阳娜娜娜娜")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="② 台签打印").click()
        await page.wait_for_timeout(200)
        nm = page.locator("#sign-preview .sign-name").first
        style = await nm.get_attribute("style") or ""
        info = await nm.evaluate("""el=>{
            const r=el.getBoundingClientRect();
            const k=el.style.transform.match(/scaleX\\(([\\d.]+)\\)/);
            return {w_layout: el.offsetWidth, w_visual: r.width, h: el.offsetHeight, k: k?+k[1]:null}
        }""")
        print(f"6字名 scaleX: {info['k']} | 布局宽 {info['w_layout']}px 视觉宽 {info['w_visual']:.0f}px 高 {info['h']}px")
        assert info["k"] is not None, "6字名应触发横向压缩"
        assert abs(info["k"] - 186/328) < 0.05, f"压缩比应约 {186/328:.3f}（155pt×6字≈328mm）"
        assert info["w_visual"] < 190*3.7795 + 10, "压缩后视觉宽应在 190mm 框内"
        assert info["h"] < 320, "压缩只影响宽度，高度应保持单行"
        # 预览区有 scale(.32)，且视觉得到的 k 应 ≈ avail/w_layout
        avail = await page.evaluate("document.querySelector('#sign-preview .std-frame').offsetWidth-75.59")  # 左右各缩进10mm
        assert abs(info["k"] - avail/info["w_layout"]) < 0.01

        # 3. 打印路径：print-area 里的长名也应用了 scaleX（隐藏状态下可测量）
        await page.evaluate("printSigns()")
        pa = await page.evaluate("""()=>{
            const els=[...document.querySelectorAll('#print-area .sign-name')];
            return els.map(el=>({t:el.style.transform, w:el.offsetWidth, pa_visible_w:el.getClientRects().length>0}));
        }""")
        print("print-area sign-name:", pa)
        assert len(pa) == 2 and pa[0]["t"].startswith("scaleX"), "打印 DOM 应同样压缩"
        assert pa[1]["t"].startswith("scaleX")
        k_print = float(pa[0]["t"].split("(")[1].rstrip(")"))
        assert abs(k_print - info["k"]) < 0.001, "打印与预览压缩比一致"

        # 4. 短名混合长名时互不影响（短名无 transform）
        await page.get_by_role("button", name="① 名单").click()
        await page.get_by_placeholder("张三｜党工委书记").fill("张三\n欧阳娜娜娜娜")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="② 台签打印").click()
        await page.wait_for_timeout(200)
        styles = await page.evaluate("[...document.querySelectorAll('#sign-preview .sign-name')].map(e=>e.style.transform||'none')")
        print("混合名单 transforms:", styles)
        # 每台签含上下两半各一个 .sign-name：张三(2)=none，欧阳6字(2)=scaleX
        assert len(styles) == 4 and styles[0] == "none" and styles[2].startswith("scaleX") and styles[3].startswith("scaleX")

        await browser.close()
        print("ALL PASS")

asyncio.run(main())
