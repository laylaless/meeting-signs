"""中键 = 纯平移：不选桌/不拖桌/不清选中；左键拖桌/点空白取消不受影响"""
import asyncio, sys
from playwright.async_api import async_playwright
URL="file:///Users/layla/.qwenpaw/workspaces/LTaxXM/meeting-signs/index.html"
EXE="/Users/layla/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=EXE)
        pg=await b.new_page(viewport={'width':1500,'height':1000})
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL)
        await pg.locator('header nav button[data-tab="seat"]').click()
        await pg.locator('#btn-add-long').click()
        await pg.wait_for_timeout(80)  # 等加桌视角跟随的 rAF 完成后再取基准
        async def tpos():
            return await pg.evaluate("""()=>{
              const t=state.venue.tables[0],v=state.venue;
              const r=document.getElementById('seat-canvas').getBoundingClientRect();
              return {x:r.left+v.view.x+t.x*v.zoom*V.PXM, y:r.top+v.view.y+t.y*v.zoom*V.PXM};
            }""")
        v0=await pg.evaluate("()=>({x:state.venue.tables[0].x,y:state.venue.tables[0].y,view:{...state.venue.view},sel:state.venue.sel})")
        pos=await tpos()
        await pg.mouse.move(pos['x'],pos['y'])
        await pg.mouse.down(button='middle')
        await pg.mouse.move(pos['x']+40,pos['y']+25,steps=3)
        await pg.mouse.up(button='middle')
        await pg.wait_for_timeout(80)
        v1=await pg.evaluate("()=>({x:state.venue.tables[0].x,y:state.venue.tables[0].y,view:{...state.venue.view},sel:state.venue.sel})")
        assert v1['x']==v0['x'] and v1['y']==v0['y'],f"桌子不应移动 {v0}->{v1}"
        assert v1['view']['x']==v0['view']['x']+40 and v1['view']['y']==v0['view']['y']+25,f"view 应平移 {v0}->{v1}"
        assert v1['sel']==v0['sel'],f"sel 不应变 {v0['sel']}->{v1['sel']}"
        print("1. 中键按在桌子上：桌子不动、画布平移 +40/+25、sel 不变 ✓")
        pos=await tpos()
        await pg.mouse.move(pos['x'],pos['y'])
        await pg.mouse.down(button='left')
        await pg.mouse.move(pos['x']-30,pos['y']-20,steps=3)
        await pg.mouse.up(button='left')
        await pg.wait_for_timeout(80)
        v2=await pg.evaluate("()=>({x:state.venue.tables[0].x,y:state.venue.tables[0].y,sel:state.venue.sel})")
        assert (v2['x'],v2['y'])!=(v1['x'],v1['y']),f"左键应能拖桌 {v1}->{v2}"
        assert v2['sel'] is not None
        print("2. 左键拖桌仍正常:",(v1['x'],v1['y']),"→",(v2['x'],v2['y']),"✓")
        p3=await pg.evaluate("""()=>{
          const r=document.getElementById('seat-canvas').getBoundingClientRect();
          return {x:r.right-30,y:r.bottom-30};
        }""")
        await pg.mouse.move(p3['x'],p3['y'])
        await pg.mouse.down(button='left');await pg.mouse.up(button='left')
        v3=await pg.evaluate("()=>state.venue.sel")
        assert v3 is None
        print("3. 左键点画布右下空白取消选中 ✓")
        assert not errs,errs
        print("PASS test_mmb2")
        await b.close()
asyncio.run(main())
