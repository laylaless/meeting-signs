import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def order_of(page):
    return await page.evaluate("buildSeats().order")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=EXE)
        page = await b.new_page()
        page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
        await page.goto(URL)

        # 1. 默认勾选镜像 + 默认 long 模板
        await page.get_by_role("button", name="③ 座位示意图").click()
        checked = await page.evaluate("()=>({box:document.getElementById('seat-mirror').checked,state:state.seat.mirror})")
        print("默认镜像:", checked)
        assert checked["box"] and checked["state"]

        # 2. 偶数 6 人/侧：1 号对 1 号、2/3 号左右互换
        await page.locator("#seat-long-count").fill("6")
        await page.wait_for_timeout(100)
        o = await order_of(page)
        print("偶数6人 order[0..11]:", o[:12])
        assert o[0] == "lt2", "上侧 1 号在 pos2"
        assert o[6] == "lb2", "下侧 1 号也应在 pos2（1 号正对 1 号）"
        assert o[7] == "lb1", "下侧 2 号镜像换边 pos1（标准 pos3）"
        assert o[8] == "lb3", "下侧 3 号在 pos3（上侧 3 号 pos1，左右互换）"
        assert o[2] == "lt1", "上侧 3 号标准序 pos1（上侧不受镜像影响）"

        # 2b. 偶数 4 人/侧：上 3124 / 下 6578（layla 给定布局）
        await page.locator("#seat-long-count").fill("4")
        await page.wait_for_timeout(100)
        o = await order_of(page)
        def row(prefix, n):
            seq = ["?"] * n
            for rank, sid in enumerate(o):
                if sid.startswith(prefix) and sid[len(prefix):].isdigit():
                    seq[int(sid[len(prefix):])] = str(rank + 1)
            return "".join(seq)
        top, bottom = row("lt", 4), row("lb", 4)
        print(f"4人/侧: 上 {top} 下 {bottom}")
        assert top == "3124" and bottom == "6578", (top, bottom)

        # 3. 奇数 5 人/侧：1 号居中对齐，2 号换边
        await page.locator("#seat-long-count").fill("5")
        await page.wait_for_timeout(100)
        o = await order_of(page)
        print("奇数5人 order[0..9]:", o[:10])
        assert o[0] == "lt2" and o[5] == "lb2", "两侧 1 号均 pos2"
        assert o[1] == "lt3" and o[6] == "lb1", "下侧 2 号镜像换边（pos3→pos1）"

        # 4. 取消勾选：下侧恢复标准序
        await page.locator("#seat-mirror").uncheck()
        await page.wait_for_timeout(100)
        o = await order_of(page)
        print("取消镜像 order[5..9]:", o[5:10])
        assert o[1] == "lt3" and o[6] == "lb3", "两侧 2 号均标准 pos3"
        assert o[7] == "lb1", "标准序下侧 3 号回 pos1"
        await page.locator("#seat-mirror").check()

        # 5. 圆桌模版镜像行为不变：mirror=true 时 2 号位 = n-1
        await page.locator("#seat-template").select_option("round")
        await page.locator("#seat-mirror").check()
        await page.locator("#seat-round-count").fill("10")
        await page.wait_for_timeout(100)
        o = await order_of(page)
        print("圆桌 order[0..2]:", o[:3])
        assert o[0] == "rd0" and o[1] == "rd9", "圆桌镜像 2 号位换边(n-1)"

        # 6. 恢复默认后仍勾选
        await page.locator("#btn-reset").click()
        await page.wait_for_timeout(100)
        checked = await page.evaluate("document.getElementById('seat-mirror').checked")
        assert checked
        print("ALL PASS")
        await b.close()

asyncio.run(main())
