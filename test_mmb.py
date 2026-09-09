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
        await pg.locator('header nav button[data-tab="seat"]').click()
        await pg.locator('#btn-add-long').click()
        await pg.wait_for_timeout(80)  # 等加桌视角跟随的 rAF 完成后再取基准

        BTN={0:'left',1:'middle',2:'right'}
        async def drag(button,dx,dy):
            v0=await pg.evaluate("()=>({...state.venue.view})")
            r=await pg.evaluate("()=>{const r=document.getElementById('seat-canvas').getBoundingClientRect();return {x:r.right-60,y:r.bottom-40}}")  # 空白角落
            await pg.mouse.move(r['x'],r['y'])
            await pg.mouse.down(button=BTN[button])
            await pg.mouse.move(r['x']+dx,r['y']+dy,steps=3)
            await pg.mouse.up(button=BTN[button])
            await pg.wait_for_timeout(60)
            return v0,await pg.evaluate("()=>({...state.venue.view})")

        # 1. 中键平移恢复
        v0,v1=await drag(1,50,30)
        assert v1['x']==v0['x']+50 and v1['y']==v0['y']+30,(v0,v1)
        print("1. 中键拖动平移 +50/+30 ✓",{v0['x']},'→',{v1['x']})
        # 2. 右键仍不平移
        v0,v2=await drag(2,60,-40)
        assert v2==v0,(v0,v2)
        print("2. 右键拖动不平移 ✓")
        # 3. 左键空白平移仍正常
        v0,v3=await drag(0,-30,20)
        assert v3['x']==v0['x']-30 and v3['y']==v0['y']+20,(v0,v3)
        print("3. 左键空白拖动平移 ✓")
        # 4. mousedown 中键被 preventDefault（autoscroll 阻止）
        pd=await pg.evaluate("""()=>{
          const c=document.getElementById('seat-canvas');
          const e=new MouseEvent('mousedown',{button:1,cancelable:true,bubbles:true});
          c.dispatchEvent(e);return e.defaultPrevented;
        }""")
        assert pd
        print("4. 中键 mousedown 已 preventDefault（防自动滚动）✓")

        print("errors:",errs); assert not errs
        print("ALL PASS")
        await b.close()
asyncio.run(main())
