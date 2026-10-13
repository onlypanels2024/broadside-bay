import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})");EB=lambda c:B.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");B.goto(U+'?who=maria');B.wait_for_timeout(2000);B.evaluate("localStorage.clear()")
  day="Math.floor(Date.now()/86400000)"
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:800,earned:0,sunk:0,xp:300,up:{hull:0,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true},ship:'brig',daily:{d:"+day+",st:1}})")
  A.evaluate("window.__fakeDb.ref('saves/google_maria').set({gold:0,earned:0,sunk:0,xp:50,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:"+day+",st:1}})")
  for pg in(A,B):
    pg.click('#goOpen');pg.wait_for_timeout(400);pg.click('#joingoogle');pg.wait_for_timeout(600);pg.click('#joingo')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  A.wait_for_timeout(1500)
  EA("openMenu()");A.wait_for_timeout(200);print('fleet button:',A.is_visible('#menufleet'));A.click('#menufleet');A.wait_for_timeout(500)
  A.screenshot(path=D+'f_none.png')
  A.evaluate("window.__rude=['Rude Name']")
  A.fill('#flname','Rude Name');A.fill('#fltag','rude');A.click('#flcreate');A.wait_for_timeout(2500);print('rude name:',A.inner_text('#fleetmsg'))
  A.fill('#flname','Sea Wolves');A.fill('#fltag','wolf');A.locator('#flcols .sw').nth(1).click();A.locator('#flems .emt').nth(1).click();A.click('#flcreate');A.wait_for_timeout(3000)
  print('founded:',A.inner_text('#fleetmsg'),'| A gold',EA("gold"),'| heading',A.inner_text('#fleeth'))
  A.screenshot(path=D+'f_mine.png');A.click('#fleetclose');EA("closeMenu()")
  # B joins
  EB("openMenu()");B.wait_for_timeout(200);B.click('#menufleet');B.wait_for_timeout(600);B.click('#fjoin-WOLF');B.wait_for_timeout(3000)
  print('B joined:',B.inner_text('#fleetmsg'),'|',B.inner_text('#fleeth'));B.click('#fleetclose');EB("closeMenu()")
  EA("P.x=60;P.z=40;P.a=0;P.v=0");EB("P.x=60;P.z=24;P.a=Math.PI;P.v=0");A.wait_for_timeout(3500)
  print('A presence fl:',A.evaluate("window.__fakeTree().players.google_gary.fl"),'| B sees A as mate:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>[r.pr.fl,isMate(r.peer)])"))
  B.screenshot(path=D+'f_mate_view.png')
  # A fires a broadside at B: no damage
  hp0=EB("P.hp")
  for i in range(4):
    EA("P.x=60;P.z=40;P.a=0;P.v=0;P.cool=0;setAim('side')");EB("P.x=60;P.z=24;P.v=0;P.inv=0")
    A.keyboard.down('Space');A.wait_for_timeout(100);A.keyboard.up('Space');A.wait_for_timeout(1300)
  print('B hp',hp0,'->',EB("P.hp"),'| referee hits:',[l for l in A.evaluate('window.__refLog') if l[0]=='hit'][:3])
  # leaderboards fleets tab
  for k in range(3):
    EA("P.x=90;P.z=70");A.wait_for_timeout(300);EA("econKill('sloop')");A.wait_for_timeout(500)
  print('errors',errs);b.close()
