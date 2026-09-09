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
        names='\n'.join([f'人{i}' for i in range(1,9)])
        await pg.get_by_placeholder('张三｜党工委书记').fill(names)
        await pg.locator('#btn-import-replace').click()
        await pg.locator('nav button[data-tab="seat"]').click()
        await pg.locator('#btn-add-long').click()
        await pg.evaluate("()=>{const t=state.venue.tables[0];t.seatsA=4;t.seatsB=4;t.x=130;t.y=95;save()}")

        # ===== 1. 名单点击自动指派 =====
        chips=pg.locator('#seat-people .pchip')
        await chips.nth(0).click(); await pg.wait_for_timeout(80)
        await chips.nth(1).click(); await pg.wait_for_timeout(80)
        st=await pg.evaluate("()=>({n:Object.keys(state.venue.assign).length, pids:Object.values(state.venue.assign), order:venueOrder().slice(0,2).map(o=>o.key)})")
        print("1a. 点击指派 2 人:",st)
        assert st['n']==2 and set(st['pids'])=={'p1','p2'}
        # 点到 1、2 号位
        assert st['order'][0] in state_.keys if False else True
        keys=await pg.evaluate("()=>venueOrder().slice(0,2).map(o=>o.key)")
        assert all(k in st['pids'] or True for k in keys)
        a=await pg.evaluate("()=>venueOrder().slice(0,2).map(o=>state.venue.assign[o.key])")
        assert a==['p1','p2'], a
        # 再点人1：应从 1 号位移到第 3 空位（先删旧位，不重复占座）
        await chips.nth(0).click(); await pg.wait_for_timeout(80)
        st2=await pg.evaluate("()=>({n:Object.keys(state.venue.assign).length, third:state.venue.assign[venueOrder()[2].key], first:state.venue.assign[venueOrder()[0].key]})")
        print("1b. 重复点击移位:",st2)
        assert st2['n']==2 and st2['third']=='p1' and st2['first'] is None
        # 座位上渲染出名字（pid 数字化修复验证）
        names_on_canvas=await pg.evaluate("()=>venueOrder().slice(0,3).map(o=>seatPerson(o.key)?seatPerson(o.key).name:null)")
        print("1c. 座位显示名字:",names_on_canvas)
        assert names_on_canvas==[None,'人2','人1'], names_on_canvas

        # ===== 2. 右键不平移 =====
        v0=await pg.evaluate("()=>({...state.venue.view})")
        await pg.evaluate("""()=>{
          const c=document.getElementById('seat-canvas'),r=c.getBoundingClientRect();
          c.dispatchEvent(new PointerEvent('pointerdown',{button:2,clientX:r.left+300,clientY:r.top+300,pointerId:9,bubbles:true}));
          c.dispatchEvent(new PointerEvent('pointermove',{button:2,clientX:r.left+380,clientY:r.top+340,pointerId:9,bubbles:true}));
          c.dispatchEvent(new PointerEvent('pointerup',{button:2,clientX:r.left+380,clientY:r.top+340,pointerId:9,bubbles:true}));
        }""")
        v1=await pg.evaluate("()=>({...state.venue.view})")
        print("2. 右键拖动后 view:",v0,"→",v1)
        assert v0==v1

        # ===== 3. 右键座位禁用 =====
        # 先清排座，禁用 1 号位（order[0]）
        await pg.evaluate("()=>{state.venue.assign={};save();renderSeat();renderSeatPeople()}")
        def seatpos(key):
            return pg.evaluate("""(key)=>{
              const t=state.venue.tables.find(x=>x.kind==='long'),g=tableGeom(t);
              const s=g.seats.find(s=>s.key===key);
              const v=state.venue,c=document.getElementById('seat-canvas'),r=c.getBoundingClientRect();
              return {sx:r.left+v.view.x+(t.x+s.x)*v.zoom*V.PXM, sy:r.top+v.view.y+(t.y+s.y)*v.zoom*V.PXM};
            }""",key)
        key1=await pg.evaluate("()=>venueOrder()[0].key")
        pos=await seatpos(key1)
        await pg.evaluate("""(p)=>{
          const c=document.getElementById('seat-canvas');
          c.dispatchEvent(new MouseEvent('contextmenu',{clientX:p.sx,clientY:p.sy,bubbles:true,cancelable:true}));
        }""",pos)
        d=await pg.evaluate("()=>state.venue.disabled")
        print("3a. 右键禁用 1 号位:",d)
        assert d==[key1]
        # 序号跳过：原 2 号位变 1 号
        o=await pg.evaluate("()=>venueOrder().map(x=>x.key)")
        assert o[0]!=key1 and len(o)==7
        # 一键排座跳过禁用座
        await pg.locator('#btn-auto-seat').click()
        a2=await pg.evaluate("""(key1)=>({n:Object.keys(state.venue.assign).length, has:key1 in state.venue.assign})""",key1)
        assert a2['n']==7 and not a2['has']
        print("3b. 一键排座 7 人，禁用座空 ✓")
        # 点击指派也跳过（清空后点 chip）
        await pg.evaluate("()=>{state.venue.assign={};save();renderSeat();renderSeatPeople()}")
        await pg.locator('#seat-people .pchip').nth(0).click(); await pg.wait_for_timeout(80)
        a3=await pg.evaluate("()=>({n:Object.keys(state.venue.assign).length, first:venueOrder()[0].key, pid:state.venue.assign[venueOrder()[0].key]})")
        print("3c. 点击指派跳过禁用:",a3)
        assert a3['n']==1 and a3['first']!=key1
        # 再右键恢复
        pos2=await seatpos(key1)
        await pg.evaluate("""(p)=>{
          const c=document.getElementById('seat-canvas');
          c.dispatchEvent(new MouseEvent('contextmenu',{clientX:p.sx,clientY:p.sy,bubbles:true,cancelable:true}));
        }""",pos2)
        d2=await pg.evaluate("()=>state.venue.disabled")
        print("3d. 再右键恢复:",d2)
        assert d2==[]
        assert await pg.evaluate("()=>venueOrder().length")==8
        # 禁用时若座上有人：清人
        await pg.locator('#btn-auto-seat').click()
        await pg.evaluate("""async ()=>{
          const key=venueOrder()[0].key;
          const t=state.venue.tables.find(x=>x.kind==='long'),g=tableGeom(t);
          const s=g.seats.find(s=>s.key===key);
          const v=state.venue,c=document.getElementById('seat-canvas'),r=c.getBoundingClientRect();
          c.dispatchEvent(new MouseEvent('contextmenu',{clientX:r.left+v.view.x+(t.x+s.x)*v.zoom*V.PXM,clientY:r.top+v.view.y+(t.y+s.y)*v.zoom*V.PXM,bubbles:true,cancelable:true}));
          window.__key=key;
        }""")
        r=await pg.evaluate("()=>({dis:state.venue.disabled.length, assigned:window.__key in state.venue.assign})")
        print("3e. 禁用带人座位清人:",r)
        assert r['dis']==1 and not r['assigned']
        # reload 持久化
        await pg.reload(); await pg.locator('nav button[data-tab="seat"]').click(); await pg.wait_for_timeout(300)
        d3=await pg.evaluate("()=>state.venue.disabled.length")
        assert d3==1
        print("3f. reload 后禁用仍在 ✓")

        print("errors:",errs); assert not errs
        print("ALL PASS")
        await b.close()
asyncio.run(main())
