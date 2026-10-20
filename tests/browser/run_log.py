import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})");EB=lambda c:B.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");B.goto(U+'?who=maria');B.wait_for_timeout(2000)
  day="Math.floor(Date.now()/86400000)"
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:900,earned:12000,sunk:80,xp:9500,dn:4,bs:7,up:{hull:0,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true,frigate:true},ship:'frigate',ks:{sloop:60,galleon:12,boss:3,kraken:1,shark:1,treasure:2,captain:11,merchant:1},daily:{d:"+day+",st:1}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  B.click('#goOpen');B.wait_for_timeout(400);B.fill('#guestname','Maria');B.click('#joinguest')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  A.wait_for_timeout(1500)
  EA("openMenu()");A.wait_for_timeout(200);A.click('#menulog');A.wait_for_timeout(600)
  print('achievements:',A.inner_text('#logcount'),'| titles offered:',A.locator('#logtitles .tchip').all_inner_texts())
  A.screenshot(path=D+'l_log.png',full_page=True)
  A.locator('#logtitles .tchip',has_text='Kraken Slayer').click();A.wait_for_timeout(300)
  for sel in ['#cos-trail2','#cos-ball1','#cos-fig2','#cos-pet1']:A.click(sel);A.wait_for_timeout(200)
  A.click('#cos-ball2');A.wait_for_timeout(200);print('locked tap:',A.inner_text('#logmsg'))
  A.wait_for_timeout(3000);sv=A.evaluate("window.__fakeTree().saves.google_gary");print('referee has title',sv.get('title'),'looks',sv.get('cx'))
  A.click('#logclose');EA("closeMenu()")
  EA("P.x=60;P.z=40;P.a=0;P.v=0");EB("P.x=60;P.z=22;P.a=0;P.v=0");A.wait_for_timeout(3500)
  print('B sees A:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>[r.pr.ti,r.pr.cx,titleOf(r.pr.ti)])"))
  EB("P.x=60;P.z=33");B.wait_for_timeout(1500);B.screenshot(path=D+'l_B_sees.png')
  # close look at the figurehead and parrot
  EA("showcase=true;Object.assign(view,{yaw:.9,pitch:.9,zoom:.55,idle:0});P.v=0");A.wait_for_timeout(2500);A.screenshot(path=D+'l_ship_close.png')
  EA("Object.assign(view,{yaw:3.6,pitch:.9,zoom:.5,idle:0})");A.wait_for_timeout(2000);A.screenshot(path=D+'l_ship_stern.png')
  EA("showcase=false;P.v=12");A.wait_for_timeout(2500);A.screenshot(path=D+'l_trail.png')
  print('errors',errs);b.close()
