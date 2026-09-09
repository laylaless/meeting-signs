import asyncio
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def setup(page, template, count, people="张三｜书记\n李四｜副书记\n王五｜委员\n赵六｜委员"):
    await page.get_by_role("button", name="① 名单").click()
    await page.get_by_placeholder("张三｜党工委书记").fill(people)
    await page.locator("#btn-import-replace").click()
    await page.get_by_role("button", name="③ 座位示意图").click()
    await page.locator("#seat-template").select_option(template)
    await page.locator("#seat-long-count").fill(str(count))
    await page.wait_for_timeout(150)

async def seat_info(page):
    return await page.evaluate("""()=>{
        const rs=[...document.querySelectorAll('#seat-svg rect[data-seat]')];
        return rs.map(r=>({id:r.dataset.seat,x:+r.getAttribute('x'),y:+r.getAttribute('y'),w:+r.getAttribute('width'),h:+r.getAttribute('height')}));
    }""")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=EXE)
        page = await b.new_page(viewport={'width':1600,'height':1000})
        await page.goto(URL)

        # 1. 新增下拉选项
        opts = await page.locator("#seat-template option").all_text_contents()
        print("布局选项:", opts)
        assert "长条桌3排" in opts and "长条桌4排" in opts

        # 2. 对坐 15 人/侧：全部座位在画布内（原 bug：>10 被 clamp 截断）
        await setup(page, "long", 15)
        seats = await seat_info(page)
        print(f"long 15: 座位数 {len(seats)}")
        assert len(seats) == 30, f"应 30 个座位，实际 {len(seats)}"
        ys = {s["y"] for s in seats}
        assert ys == {36, 158}, ys
        for s in seats:
            assert 0 <= s["x"] and s["x"]+s["w"] <= 297 and s["y"]+s["h"] <= 210, s

        # 3. 4 字名 + 20 人/侧：字号随座位框缩小
        await page.get_by_role("button", name="① 名单").click()
        await page.get_by_placeholder("张三｜党工委书记").fill("欧阳夏丹｜委员\n司马文章｜委员")
        await page.locator("#btn-import-replace").click()
        await page.get_by_role("button", name="③ 座位示意图").click()
        await page.locator("#btn-auto-seat").click()
        await page.wait_for_timeout(150)
        fs = await page.evaluate("""()=>{
            const ts=[...document.querySelectorAll('#seat-svg text')];
            const named=ts.filter(x=>['欧阳夏丹','司马文章'].includes(x.textContent));
            return named.map(x=>+x.getAttribute('font-size'));
        }""")
        w_min = min(s["w"] for s in await seat_info(page))
        print(f"long 20: 座位框最小宽 {w_min:.1f}mm, 4字名字号 {fs}")
        expect_fs = round(min(9, (w_min-2)/(4*0.3528)), 1)  # v1 最终 seatFont 口径
        assert all(abs(f-expect_fs) < 0.06 for f in fs), (fs, expect_fs)

        # 4. long3：上1排 + 下2排
        await setup(page, "long3", 6)
        seats = await seat_info(page)
        ys = sorted({s["y"] for s in seats})
        idset = {s["id"] for s in seats}
        print(f"long3: 座位 {len(seats)}, y 排 {ys}, 含 lb20: {'lb20' in idset}")
        assert len(seats) == 18 and ys == [36, 158, 178]
        assert "lb20" in idset, "下后排座位 id 应为 lb2x"

        # 5. long4：上下各2排
        await setup(page, "long4", 6)
        seats = await seat_info(page)
        ys = sorted({s["y"] for s in seats})
        idset = {s["id"] for s in seats}
        print(f"long4: 座位 {len(seats)}, y 排 {ys}, 含 lt20/lb20: {'lt20' in idset}/{'lb20' in idset}")
        assert len(seats) == 24 and ys == [16, 36, 158, 178]
        assert "lt20" in idset and "lb20" in idset

        # 6. 一键排座：第 1 人（张三）应排到上主排 lt 礼宾首位
        await setup(page, "long3", 5)
        await page.locator("#btn-auto-seat").click()
        await page.wait_for_timeout(150)
        first_seat = await page.evaluate("""()=>{
            const me=state.people[0];
            return Object.entries(state.seat.assignments).find(([,v])=>v===me.id)[0];
        }""")
        print("张三座位:", first_seat)
        import re as _re
        assert first_seat.startswith("lt") and not _re.match(r"lt2\d", first_seat), "第1人应在上主排（lt2\\d 才是上后排）"

        # 7. 桌面矩形存在于 long3/long4
        for tpl in ["long3","long4"]:
            await page.locator("#seat-template").select_option(tpl)
            await page.wait_for_timeout(100)
            has_desk = await page.evaluate("""()=>[...document.querySelectorAll('#seat-svg rect')].some(r=>!r.dataset.seat&&+r.getAttribute('width')===169)""")
            assert has_desk, f"{tpl} 应有桌面矩形"
        print("桌面绘制 OK")

        await b.close()
        print("ALL PASS")

asyncio.run(main())
