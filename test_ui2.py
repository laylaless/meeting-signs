import asyncio
from playwright.async_api import async_playwright
URL="file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE="/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=EXE)
        pg=await b.new_page(viewport={'width':1500,'height':1000})
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL)
        names='\n'.join([f'人{i}' for i in range(1,7)])
        await pg.get_by_placeholder('张三｜党工委书记').fill(names)
        await pg.locator('#btn-import-replace').click()
        await pg.locator('nav button[data-tab="seat"]').click()

        # ===== 1. 三个侧栏卡片可折叠 =====
        cards=['tableprop','tables','people']
        for cid in cards:
            c=pg.locator(f'.card.collapsible[data-col="{cid}"]')
            h=c.locator('h2')
            v0=await c.locator('#table-prop, #table-form, .plist').first.is_visible()
            await h.click(); await pg.wait_for_timeout(60)
            v1=await c.locator('#table-prop, #table-form, .plist').first.is_visible()
            await h.click(); await pg.wait_for_timeout(60)
            v2=await c.locator('#table-prop, #table-form, .plist').first.is_visible()
            assert v0 and not v1 and v2, (cid,v0,v1,v2)
        print("1a. 桌子属性/桌子管理/名单 三卡折叠+展开 ✓")
        # 折叠状态持久化
        await pg.locator('.card[data-col="tables"] h2').click()
        await pg.reload(); await pg.locator('nav button[data-tab="seat"]').click(); await pg.wait_for_timeout(300)
        v=await pg.locator('.card[data-col="tables"] #table-form').is_visible()
        assert not v
        print("1b. 折叠状态 reload 保持 ✓")
        await pg.locator('.card[data-col="tables"] h2').click()  # 展开还原

        # ===== 2. 左右两列：左编辑工具 / 右会议室+JSON 管理 =====
        pos=await pg.evaluate("""()=>{
          const ecEl=document.querySelector('.editor-card'),vcEl=document.querySelector('.venue-card');
          const ec=ecEl.getBoundingClientRect(),cv=document.querySelector('.seat-canvas-wrap').getBoundingClientRect();
          const vc=vcEl.getBoundingClientRect(),tp=document.querySelector('.card[data-col="tableprop"]').getBoundingClientRect();
          return {ecInMain:!!ecEl.closest('.seat-main'), ecAboveCanvas:ec.bottom<=cv.top+1,
                  vcInSide:!!vcEl.closest('.seat-side'), vcAboveTP:vc.bottom<=tp.top+1,
                  vTitle:document.querySelector('.venue-card h2').textContent, vcCollapse:vcEl.classList.contains('collapsible')};
        }""")
        assert pos['ecInMain'] and pos['ecAboveCanvas'] and pos['vcInSide'] and pos['vcAboveTP'] and pos['vTitle']=='会议室管理' and pos['vcCollapse'], pos
        print("2a. 会场编辑在 seat-main 画布上方；会议室管理在侧栏桌子属性上方、可折叠 ✓")
        # 侧栏已无会议室库卡片
        n=await pg.locator('.seat-side .card h2',has_text='会议室库').count()
        assert n==0
        print("2b. 侧栏已无会议室库卡片 ✓")
        # 保存/载入仍工作
        await pg.locator('#btn-add-long').click()
        await pg.locator('#venue-name-input').fill('测试会议室')
        await pg.locator('#btn-save-venue').click(); await pg.wait_for_timeout(100)
        chips=await pg.locator('#venue-lib .trow').count()
        assert chips==1
        await pg.locator('#venue-lib .trow button[data-act="load"]').click()
        await pg.wait_for_timeout(100)
        tn=await pg.evaluate("()=>state.venue.tables.length")
        assert tn==1
        print("2c. 保存为会议室 + chips 载入 ✓")

        # ===== 3. 备份三按钮在 banner，与 tab 区分 =====
        v3=await pg.evaluate("""()=>{
          const h=document.querySelector('header').getBoundingClientRect();
          const inB=id=>{const r=document.getElementById(id).getBoundingClientRect();return r.top>=h.top&&r.bottom<=h.bottom};
          const tab=document.querySelector('header nav button').getBoundingClientRect();
          const op=document.getElementById('btn-export-venue').getBoundingClientRect();
          const sep=document.querySelector('.banner-sep');
          return {exp:inB('btn-export-venue'),imp:inB('btn-import-venue'),rst:inB('btn-reset'),
                  rightOfTabs:op.left>tab.right, sep:!!sep, sepRight:sep.getBoundingClientRect().left>tab.right};
        }""")
        print("3. 备份按钮组:",v3)
        assert v3['exp'] and v3['imp'] and v3['rst'] and v3['rightOfTabs'] and v3['sep'] and v3['sepRight']

        print("errors:",errs); assert not errs
        print("ALL PASS")
        await pg.screenshot(path='preview_ui2.png')
        await b.close()
asyncio.run(main())
