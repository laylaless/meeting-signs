import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def seat_names(page):
    """返回 {seatId: 名字}"""
    return await page.evaluate("""() => {
        const A = state.seat.assignments;
        const out = {};
        for (const [sid, pid] of Object.entries(A)) {
            const p = state.people.find(x=>x.id===pid);
            out[sid] = p ? p.name : '?';
        }
        return out;
    }""")

async def drag(page, from_el, to_el):
    fb, tb = await from_el.bounding_box(), await to_el.bounding_box()
    fx, fy = fb["x"]+fb["width"]/2, fb["y"]+fb["height"]/2
    tx, ty = tb["x"]+tb["width"]/2, tb["y"]+tb["height"]/2
    await page.mouse.move(fx, fy)
    await page.mouse.down()
    steps = 10
    for i in range(1, steps+1):
        await page.mouse.move(fx+(tx-fx)*i/steps, fy+(ty-fy)*i/steps)
    await page.mouse.up()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=EXE)
        page = await browser.new_page(viewport={"width": 1400, "height": 1000})
        await page.goto(URL)
        await page.get_by_placeholder("张三｜党工委书记").fill(
            "张三\n李四\n王五\n赵六\n钱七\n孙八\n周九\n吴十\n郑一\n冯二\n陈三\n楚四")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="③ 座位示意图").click()
        await page.locator("#seat-template").select_option("combo")   # 显式指定（默认模板可能变化）
        await page.locator("#seat-mirror").uncheck()                  # 本测试只测拖拽，固定标准序
        await page.locator("#btn-auto-seat").click()
        # 追加导入第 13 人（未排）
        await page.get_by_role("button", name="① 名单").click()
        await page.get_by_placeholder("张三｜党工委书记").fill("褚五")
        await page.locator("#btn-import-append").click()
        await page.get_by_role("button", name="③ 座位示意图").click()

        before = await seat_names(page)
        print("一键排座:", before)
        assert before.get("st3") == "张三", "1 号位应居中"
        assert len(before) == 12, f"12 人已排、褚五未排，实际 {len(before)}"

        # --- 1. 名单拖到空座位（圆桌 rd5） ---
        item_un = page.locator("#seat-people .pitem").nth(12)          # 褚五（未排）
        rd5 = page.locator('#seat-svg rect[data-seat="rd5"]')
        await drag(page, item_un, rd5)
        after = await seat_names(page)
        print("名单→圆桌空位 rd5:", after.get("rd5"))
        assert after.get("rd5") == "褚五" and len(after) == 13

        # --- 2. 主席台座位间互换（张三 st3 ↔ 李四 st4） ---
        st3 = page.locator('#seat-svg rect[data-seat="st3"]')
        st4 = page.locator('#seat-svg rect[data-seat="st4"]')
        await drag(page, st3, st4)
        after2 = await seat_names(page)
        print("互换后 st3/st4:", after2.get("st3"), after2.get("st4"))
        assert after2.get("st3") == "李四" and after2.get("st4") == "张三"

        # --- 3. 拖到空白处撤销（把 st0 周九拖走） ---
        st0 = page.locator('#seat-svg rect[data-seat="st0"]')
        fb = await st0.bounding_box()
        await page.mouse.move(fb["x"]+20, fb["y"]+8)
        await page.mouse.down()
        for i in range(1, 11):
            await page.mouse.move(fb["x"]+20+30*i, fb["y"]+8-40)  # 拖向主席台上空白
        await page.mouse.up()
        after3 = await seat_names(page)
        print("拖空白撤销 st0:", after3.get("st0"))
        assert "st0" not in after3

        # --- 4. 点击行为不受影响（等防误触窗口过后：点座位选中 → 点名单指派） ---
        await page.wait_for_timeout(200)
        st1 = page.locator('#seat-svg rect[data-seat="st1"]')
        await st1.click()
        selected = await page.evaluate("state.selectedSeat")
        print("点击选中:", selected)
        assert selected == "st1"
        item_unb = page.locator("#seat-people .pitem").nth(12)
        await item_unb.click()
        after4 = await seat_names(page)
        print("点名单指派 st1:", after4.get("st1"))
        assert after4.get("st1") == "褚五"

        # --- 5. 幽灵已清理、无残留监听状态 ---
        ghosts = await page.locator(".drag-ghost").count()
        assert ghosts == 0, ghosts
        # 拖拽后立刻点另一座位不应被 suppress 吞掉
        await page.wait_for_timeout(150)
        await st4.click()
        assert await page.evaluate("state.selectedSeat") == "st4"

        await page.evaluate("localStorage.clear()")
        await browser.close()
        print("ALL PASS")

asyncio.run(main())
