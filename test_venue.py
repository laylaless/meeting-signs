import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE = "/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"
PXM = 3.7795

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=EXE)
        pg = await b.new_page(viewport={'width': 1500, 'height': 1000})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL)

        # 1. 添加三种桌型
        await pg.get_by_role("button", name="③ 座位示意图").click() if await pg.get_by_role("button", name="③ 座位示意图").count() else await pg.locator('nav button[data-tab="seat"]').click()
        await pg.locator("#btn-add-podium").click()
        await pg.locator("#btn-add-round").click()
        await pg.locator("#btn-add-long").click()
        await pg.wait_for_timeout(200)
        st = await pg.evaluate("() => state.venue.tables.map(t => ({no:t.no, kind:t.kind, x:t.x, y:t.y, rot:t.rot}))")
        print("1. 三桌:", st)
        assert len(st) == 3 and [t['kind'] for t in st] == ['podium', 'round', 'long']
        assert [t['no'] for t in st] == [1, 2, 3]

        # 2. 座位数调整：选中 3 号长条桌，上侧改 8
        await pg.evaluate("() => { state.venue.sel = state.venue.tables.find(t=>t.no===3).id; renderTableProp() }")
        await pg.locator("#tp-a").fill("8")
        await pg.locator("#tp-a").dispatch_event("change")
        await pg.wait_for_timeout(100)
        t3 = await pg.evaluate("() => state.venue.tables.find(t=>t.no===3)")
        print("2. 长条桌座位:", t3['seatsA'], "+", t3['seatsB'])
        assert t3['seatsA'] == 8

        # 3. 旋转 + 翻转
        await pg.locator("#tp-rot").click()
        await pg.locator("#tp-flip").click()
        t3 = await pg.evaluate("() => state.venue.tables.find(t=>t.no===3)")
        print("3. 旋转/翻转:", t3['rot'], t3['flip'])
        assert t3['rot'] == 90 and t3['flip'] is True

        # 4. 拖动桌子位置（canvas pointer 拖拽）
        rect = await pg.locator("#seat-canvas").bounding_box()
        zoom, view = await pg.evaluate("() => [state.venue.zoom, state.venue.view]")
        t3 = await pg.evaluate("() => state.venue.tables.find(t=>t.no===3)")
        sx = rect['x'] + t3['x'] * zoom * PXM + view['x']
        sy = rect['y'] + t3['y'] * zoom * PXM + view['y']
        await pg.mouse.move(sx, sy)
        await pg.mouse.down()
        await pg.mouse.move(sx + 120, sy + 80, steps=6)
        await pg.mouse.up()
        t3b = await pg.evaluate("() => state.venue.tables.find(t=>t.no===3)")
        print("4. 拖桌: (%d,%d) -> (%d,%d)" % (t3['x'], t3['y'], t3b['x'], t3b['y']))
        assert abs(t3b['x'] - t3['x']) > 20 and abs(t3b['y'] - t3['y']) > 10

        # 5. 缩放：按钮 + 滚轮
        z0 = await pg.evaluate("() => state.venue.zoom")
        await pg.locator("#btn-zoom-in").click()
        z1 = await pg.evaluate("() => state.venue.zoom")
        await pg.mouse.move(rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2)
        await pg.mouse.wheel(0, -300)
        z2 = await pg.evaluate("() => state.venue.zoom")
        print("5. 缩放:", z0, "->", z1, "->", z2)
        assert z1 > z0 and z2 > z1
        await pg.locator("#btn-zoom-fit").click()
        zf = await pg.evaluate("() => state.venue.zoom")
        print("   fit 后:", round(zf, 3))

        # 6. 表单编号顺序：把 1 号（主席台）下移
        row = pg.locator('#table-form .trow').first
        await row.locator('[data-act="down"]').click()
        nos = await pg.evaluate("() => state.venue.tables.slice().sort((a,b)=>a.no-b.no).map(t=>t.kind)")
        print("6. 编号顺序:", nos)
        assert nos == ['round', 'podium', 'long']

        # 7. 一键排座（先导入名单）
        await pg.evaluate("() => { document.querySelector('nav button[data-tab=list]').click() }")
        await pg.get_by_placeholder("张三｜党工委书记").fill("张三｜书记\n李四｜主任\n王五｜委员\n赵六\n钱七\n孙八\n周九\n吴十\n郑一\n王二\n冯三\n陈四")
        await pg.locator("#btn-import-replace").click()
        await pg.locator('nav button[data-tab="seat"]').click()
        await pg.wait_for_timeout(200)
        await pg.locator("#btn-auto-seat").click()
        n_assign = await pg.evaluate("() => Object.keys(state.venue.assign).length")
        order1 = await pg.evaluate("() => venueOrder()[0]")
        print("7. 一键排座: %d 人, 1号位 key=%s no=%d" % (n_assign, order1['key'], order1['no']))
        assert n_assign == 12 and order1['no'] == 1

        # 8. 礼宾序号语义：圆桌主位在底部（1 号桌现在是圆桌）
        seat_pos = await pg.evaluate("""() => {
          const t = state.venue.tables.find(t => t.kind === 'round');
          const g = tableGeom(t);
          const key = venueOrder()[0].key;
          return g.seats.find(s => s.key === key);
        }""")
        print("8. 1号位（圆桌主位应近底部 y>0）:", seat_pos)
        assert seat_pos['y'] > 0

        # 9. 打印渲染：按当前 zoom（≥铺满 A4 比例）输出，画布尺寸与物理尺寸自洽
        ok = await pg.evaluate("""() => {
          const c = renderHiRes(8, 'print');
          return Math.abs(c.width / 8 - c._wmm) < 1 && Math.abs(c.height / 8 - c._hmm) < 1 && c.width > 0
        }""")
        print("9. 打印 canvas:", ok)
        assert ok

        # 10. localStorage 持久化 + reload 恢复
        await pg.reload()
        await pg.locator('nav button[data-tab="seat"]').click()
        await pg.wait_for_timeout(300)
        st2 = await pg.evaluate("() => ({tables: state.venue.tables.length, assign: Object.keys(state.venue.assign).length})")
        print("10. reload 恢复:", st2)
        assert st2['tables'] == 3 and st2['assign'] == 12

        # 11. 导出会场 JSON：文件结构校验（先存一个会议室，验证库随 JSON 导出）
        await pg.locator("#venue-name-input").fill("会议室A")
        await pg.locator("#btn-save-venue").click()
        await pg.wait_for_timeout(200)
        async with pg.expect_download() as dl_info:
            await pg.locator("#btn-export-venue").click()
        dl = await dl_info.value
        path = "/tmp/venue_export_test.json"
        await dl.save_as(path)
        data = json.load(open(path, encoding='utf-8'))
        print("11. 导出 JSON:", {'format': data.get('format'), 'people': len(data.get('people', [])),
              'tables': len(data['venue']['tables']), 'assign': len(data['venue']['assign']),
              'venueLib': len(data.get('venueLib', []))})
        assert data['app'] == 'meeting-signs' and data['format'] == 'venue' and data['version'] == 4
        assert len(data['venue']['tables']) == 3
        assert data['venue']['tables'][0]['kind'] in ('long', 'round', 'podium')
        assert len(data['venueLib']) == 1 and data['venueLib'][0]['name'] == '会议室A'

        # 12. 导入恢复：先清空（含会议室库），再导入刚导出的文件
        await pg.evaluate("() => { state.venue = {tables:[],assign:{},sel:null,selSeat:null,showNo:true,zoom:1,view:{x:40,y:30}}; state.people=[]; saveVenues([]); save(); renderPeopleTable(); renderSeatPeople(); renderTableProp(); renderTableForm(); renderSeat(); renderVenueLib(); }")
        st3 = await pg.evaluate("() => ({tables: state.venue.tables.length, people: state.people.length, lib: loadVenues().length})")
        assert st3 == {'tables': 0, 'people': 0, 'lib': 0}
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.locator("#venue-json-file").set_input_files(path)
        await pg.wait_for_timeout(400)
        st4 = await pg.evaluate("() => ({tables: state.venue.tables.length, assign: Object.keys(state.venue.assign).length, people: state.people.length, lib: loadVenues().map(v=>v.name)})")
        print("12. 导入后恢复:", st4)
        assert st4['tables'] == 3 and st4['assign'] == 12 and st4['people'] > 0
        assert st4['lib'] == ['会议室A']
        # 导入后已自动存 localStorage：reload 仍在
        await pg.reload()
        await pg.locator('nav button[data-tab="seat"]').click()
        await pg.wait_for_timeout(300)
        st5 = await pg.evaluate("() => ({tables: state.venue.tables.length, people: state.people.length})")
        print("    导入后 reload:", st5)
        assert st5 == {'tables': 3, 'people': st4['people']}

        # 13. 导入坏文件：缺 format:venue，状态不变
        bad = "/tmp/venue_bad_test.json"
        open(bad, 'w').write('{"foo": 1}')
        n_before = await pg.evaluate("() => state.venue.tables.length")
        await pg.locator("#venue-json-file").set_input_files(bad)
        await pg.wait_for_timeout(300)
        n_after = await pg.evaluate("() => state.venue.tables.length")
        print("13. 坏文件导入被拒:", n_before, "->", n_after)
        assert n_before == n_after

        # 14. 保存为会议室：当前 3 桌存成「三楼大会议室」
        await pg.locator("#venue-name-input").fill("三楼大会议室")
        await pg.locator("#btn-save-venue").click()
        await pg.wait_for_timeout(200)
        lib = await pg.evaluate("() => loadVenues()")
        print("14. 保存会议室:", [(v['name'], len(v['tables'])) for v in lib])
        assert len(lib) == 2 and lib[1]['name'] == '三楼大会议室' and len(lib[1]['tables']) == 3
        assert await pg.locator("#venue-lib .trow").count() == 2

        # 15. 清空画布后载入第一行（会议室A）：布局恢复、排座清空、名单保留
        await pg.evaluate("() => { state.venue.tables=[]; state.venue.assign={}; save(); renderTableProp(); renderTableForm(); renderSeat(); }")
        await pg.locator("#venue-lib button[data-act='load']").first.click()
        await pg.wait_for_timeout(300)
        st6 = await pg.evaluate("() => ({tables: state.venue.tables.length, kinds: state.venue.tables.map(t=>t.kind), assign: Object.keys(state.venue.assign).length, people: state.people.length})")
        print("15. 载入会议室:", st6)
        assert st6['tables'] == 3 and st6['kinds'] == ['podium', 'round', 'long'] and st6['assign'] == 0 and st6['people'] > 0

        # 16. reload 后会议室库仍在（独立 LS key）；再存第二个会议室
        await pg.reload()
        await pg.locator('nav button[data-tab="seat"]').click()
        await pg.wait_for_timeout(300)
        lib2 = await pg.evaluate("() => loadVenues()")
        assert [v['name'] for v in lib2] == ['会议室A', '三楼大会议室']
        await pg.locator("#btn-add-long").click()
        await pg.locator("#venue-name-input").fill("小会议室")
        await pg.locator("#btn-save-venue").click()
        await pg.wait_for_timeout(200)
        lib3 = await pg.evaluate("() => loadVenues().map(v => v.name)")
        print("16. reload 后库仍在 + 第二会议室:", lib3)
        assert lib3 == ['会议室A', '三楼大会议室', '小会议室']

        # 17. 重名保存覆盖 + 删除
        await pg.locator("#venue-name-input").fill("小会议室")
        await pg.locator("#btn-save-venue").click()
        await pg.wait_for_timeout(200)
        assert await pg.evaluate("() => loadVenues().length") == 3
        rows = pg.locator("#venue-lib .trow")
        await rows.nth(1).locator("button[data-act='del']").click()
        await pg.wait_for_timeout(200)
        lib4 = await pg.evaluate("() => loadVenues().map(v => v.name)")
        print("17. 覆盖重名 + 删除:", lib4)
        assert lib4 == ['会议室A', '小会议室']
        # 清理测试库
        await pg.evaluate("() => saveVenues([])")
        # 前面 dialog handler 自动 accept，恢复默认不让它误伤：无

        print("页面错误:", errs if errs else "无")
        assert not errs
        print("ALL PASS")
        await b.close()

asyncio.run(main())
