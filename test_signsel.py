import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=EXE)
        page = await b.new_page()
        alerts = []
        page.on("dialog", lambda d: (alerts.append(d.message), asyncio.ensure_future(d.accept())))
        await page.goto(URL)
        await page.get_by_placeholder("张三｜党工委书记").fill("张三｜书记\n李四｜副书记\n王五｜委员")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="② 台签打印").click()

        # 1. 全部选中：3 chips + 3 台签 + 按钮文案
        chips = await page.locator(".person-chip").count()
        names = await page.evaluate("[...document.querySelectorAll('.sign-name')].map(e=>e.textContent)")
        hint = await page.locator("#sign-selected-hint").inner_text()
        print(f"chips:{chips} 台签名:{sorted(set(names))} hint:{hint}")
        assert chips == 3 and sorted(set(names)) == ["张\u3000三", "李\u3000四", "王\u3000五"]  # 2字名含全角空格
        assert "3/3" in hint

        # 2. 取消张三：预览剩 2 人，持久化
        await page.locator(".person-chip", has_text="张三").locator("input").uncheck()
        names = await page.evaluate("[...document.querySelectorAll('.sign-name')].map(e=>e.textContent)")
        hint = await page.locator("#sign-selected-hint").inner_text()
        print(f"取消后:{sorted(set(names))} hint:{hint}")
        assert sorted(set(names)) == ["李\u3000四", "王\u3000五"] and "2/3" in hint
        await page.reload()
        await page.get_by_role("button", name="② 台签打印").click()
        chk = await page.locator(".person-chip", has_text="张三").locator("input").is_checked()
        names = await page.evaluate("[...document.querySelectorAll('.sign-name')].map(e=>e.textContent)")
        assert chk is False and sorted(set(names)) == ["李\u3000四", "王\u3000五"], "勾选状态应持久化"
        print("持久化 OK")

        # 3. 全不选：预览提示 + 打印被拦截
        await page.locator("#btn-sign-none").click()
        txt = await page.locator("#sign-preview").inner_text()
        assert "未勾选" in txt, txt
        await page.evaluate("window.print=()=>{}")
        await page.locator("#btn-print-sign").click()
        assert any("未勾选" in a for a in alerts), alerts
        print("空选拦截 OK:", alerts)

        # 4. 全选恢复；名单新增人员默认选中
        await page.locator("#btn-sign-all").click()
        names = await page.evaluate("[...document.querySelectorAll('.sign-name')].map(e=>e.textContent)")
        assert sorted(set(names)) == ["张\u3000三", "李\u3000四", "王\u3000五"]
        await page.get_by_role("button", name="① 名单").click()
        await page.get_by_placeholder("张三｜党工委书记").fill("赵六｜委员")
        await page.locator("#btn-import-append").click()
        await page.get_by_role("button", name="② 台签打印").click()
        names = await page.evaluate("[...document.querySelectorAll('.sign-name')].map(e=>e.textContent)")
        hint = await page.locator("#sign-selected-hint").inner_text()
        print("追加赵六后:", sorted(set(names)), hint)
        assert sorted(set(names)) == ["张\u3000三", "李\u3000四", "王\u3000五", "赵\u3000六"] and "4/4" in hint

        # 5. 恢复默认 → excluded 清空全选
        await page.locator(".person-chip", has_text="李四").locator("input").uncheck()
        await page.locator("#btn-reset").click()
        await page.wait_for_timeout(100)
        hint = await page.locator("#sign-selected-hint").inner_text()
        chk = await page.locator(".person-chip", has_text="李四").locator("input").is_checked()
        print("恢复默认后:", hint, chk)
        assert "4/4" in hint and chk

        # 6. strip 模式同样受勾选过滤
        await page.locator("#sign-mode").select_option("strip")
        await page.locator(".person-chip", has_text="张三").locator("input").uncheck()
        await page.wait_for_timeout(100)
        names = await page.evaluate("[...document.querySelectorAll('#sign-preview .sign-name')].map(e=>e.textContent)")
        print("strip 模式:", sorted(set(names)))
        assert sorted(set(names)) == ["李\u3000四", "王\u3000五", "赵\u3000六"]

        await b.close()
        print("ALL PASS")

asyncio.run(main())
