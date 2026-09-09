import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=EXE)
        page = await browser.new_page()
        await page.goto(URL)

        # 1. 默认选中标准模版 + 华文新魏
        mode = await page.locator("#sign-mode").input_value()
        font = await page.locator("#sign-font").input_value()
        print("默认样式:", mode, "| 默认字体:", font)
        assert mode == "standard" and font == "xinwei"

        # 2. 导入名单，检查预览
        await page.get_by_placeholder("张三｜党工委书记").fill("张三｜党工委书记\n李四")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="② 台签打印").click()

        frames = page.locator("#sign-preview .std-frame")
        print("std-frame 数量:", await frames.count())
        assert await frames.count() == 2

        # 3. 方框尺寸 = 190x178mm（预览有 scale(0.32)，headless 96dpi: 1mm=3.7795px）
        b = await frames.first.bounding_box()
        wmm, hmm = b["width"] / 3.7795 / 0.32, b["height"] / 3.7795 / 0.32
        print(f"方框实测(还原缩放): {wmm:.1f} x {hmm:.1f} mm")
        assert abs(wmm - 190) < 1.5 and abs(hmm - 178) < 1.5

        # 4. 名字字体 + 字号 155pt（固定，所有名字统一）
        nm = page.locator("#sign-preview .sign-name").first
        fs = await nm.get_attribute("style")
        print("sign-name style:", fs)
        assert "STXinwei" in fs and "155pt" in fs
        nm2 = page.locator("#sign-preview .sign-name").nth(1)
        fs2 = await nm2.get_attribute("style")
        assert "155pt" in fs2, "2 字名与 3 字名字号应一致"

        # 5. 上下布局：两个 std-half，第一个带 rev（对折立放后两面正向）
        halves = page.locator("#sign-preview .std-frame").first.locator(".std-half")
        assert await halves.count() == 2
        cls1 = await halves.nth(0).get_attribute("class")
        t1 = await halves.nth(0).inner_text()
        t2 = await halves.nth(1).inner_text()
        print("上半 class:", cls1, "| 下半内容:", t2.strip())
        assert "rev" in cls1 and t1.strip() == "张　三" == t2.strip()  # 2字名中间加全角空格

        # 6. 显示职务小字（96*0.22≈21pt）
        await page.locator("#sign-show-title").check()
        ts = await page.locator("#sign-preview .sign-title").first.get_attribute("style")
        print("职务小字 style:", ts)
        assert "34pt" in ts

        # 7. 切到 fold 再切回 standard：字体保持所选（0.1.1 起标准模版不再锁定华文新魏）
        await page.locator("#sign-mode").select_option("fold")
        await page.locator("#sign-font").select_option("hei")
        await page.locator("#sign-mode").select_option("standard")
        font2 = await page.locator("#sign-font").input_value()
        print("切回 standard 后字体:", font2)
        assert font2 == "hei"

        # 8. v1/v2 老数据迁移：名单保留、台签设置重置为 standard/155pt
        for oldkey in ("meeting-signs-v1", "meeting-signs-v2"):
            await page.evaluate("""(k) => {
                localStorage.clear();
                localStorage.setItem(k, JSON.stringify({
                  people:[{id:'p1',name:'王五',title:''}],
                  sign:{mode:'fold',perPage:4,size:88,font:'hei',showTitle:false},
                  seat:{template:'round'}, nextPid:2}));
            }""", oldkey)
            await page.reload()
            await page.get_by_role("button", name="② 台签打印").click()
            mode3 = await page.locator("#sign-mode").input_value()
            sz = await page.locator("#sign-preview .sign-name").first.get_attribute("style")
            names = await page.eval_on_selector_all("#people-table tbody tr td:nth-child(2)", "els=>els.map(e=>e.textContent)")
            print(f"{oldkey} 迁移后: 样式={mode3} 名单={names} style={sz[:60]}")
            assert mode3 == "standard" and names == ["王五"] and "155pt" in sz
        v3 = await page.evaluate("localStorage.getItem('meeting-signs-v4')")
        assert v3 and '"mode":"standard"' in v3

        await page.evaluate("localStorage.clear()")
        await browser.close()
        print("ALL PASS")

asyncio.run(main())
