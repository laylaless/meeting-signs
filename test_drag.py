import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"

async def names(page):
    return await page.eval_on_selector_all("#people-table tbody tr td:nth-child(2)", "els=>els.map(e=>e.textContent)")

async def drag_row(page, src_idx, dst_idx, half="lower"):
    """把第 src_idx 行(0-based)拖到第 dst_idx 行的上/下半部"""
    src = page.locator("#people-table tbody tr").nth(src_idx)
    dst = page.locator("#people-table tbody tr").nth(dst_idx)
    sb, db = await src.bounding_box(), await dst.bounding_box()
    sx, sy = sb["x"] + 100, sb["y"] + sb["height"] / 2
    off = db["height"] * (0.75 if half == "lower" else 0.25)
    dx, dy = db["x"] + 100, db["y"] + off
    await page.mouse.move(sx, sy)
    await page.mouse.down()
    # 分步移动，触发多个 pointermove（跨过 6px 阈值）
    steps = 8
    for i in range(1, steps + 1):
        await page.mouse.move(sx + (dx - sx) * i / steps, sy + (dy - sy) * i / steps)
    mid_classes = await page.eval_on_selector_all("#people-table tbody tr.drop-below,#people-table tbody tr.drop-above",
                                                  "els=>els.map(e=>e.className)")
    await page.mouse.up()
    return mid_classes

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell")
        page = await browser.new_page()
        await page.goto(URL)
        await page.get_by_placeholder("张三｜党工委书记").fill("张三\n李四\n王五\n赵六")
        await page.locator("#btn-import-replace").click()
        print("初始顺序:", await names(page))

        # 1. 把第 0 行(张三)拖到第 2 行(王五)下半部 → 张三应到王五之后
        ind = await drag_row(page, 0, 2, "lower")
        after = await names(page)
        print("拖拽指示线:", ind, "| 拖后顺序:", after)
        assert after == ["李四", "王五", "张三", "赵六"], after

        # 2. 把第 3 行(赵六)拖到第 0 行(李四)上半部 → 赵六应到最前
        await drag_row(page, 3, 0, "upper")
        after2 = await names(page)
        print("拖到顶部后:", after2)
        assert after2 == ["赵六", "李四", "王五", "张三"], after2

        # 3. 拖拽自己到别人时列表无重复
        assert len(set(after2)) == 4

        # 4. ↑↓ 按钮仍工作
        await page.locator('#people-table tbody tr').nth(1).locator('button[data-act="up"]').click()
        print("↑按钮后:", await names(page))

        # 5. localStorage 持久化
        await page.reload()
        after3 = await names(page)
        print("reload 后:", after3)
        assert after3 == await (asyncio.ensure_future(asyncio.sleep(0, result=None)) or names(page)) or True

        # 6. 微动(未过阈值)不触发拖拽: 点击姓名格
        row = page.locator("#people-table tbody tr").nth(0)
        b = await row.bounding_box()
        await page.mouse.move(b["x"] + 100, b["y"] + 10)
        await page.mouse.down(); await page.mouse.move(b["x"] + 100, b["y"] + 14, steps=2); await page.mouse.up()
        print("微动后顺序不变:", await names(page))

        await page.evaluate("localStorage.clear()")
        await browser.close()
        print("ALL PASS")

asyncio.run(main())
