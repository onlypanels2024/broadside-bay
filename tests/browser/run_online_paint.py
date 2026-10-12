import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})");EB=lambda c:B.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");B.goto(U+'?who=maria');B.wait_for_timeout(2500)
  # the referee already has Gary as a Captain owning a Frigate
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:300,earned:0,sunk:0,xp:3200,up:{hull:0,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true,frigate:true},ship:'brig'})")
  # sign in, go back to the main menu, then open the shipwright
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(800);A.click('#joinback');A.wait_for_timeout(1500)
  print('start note:',A.inner_text('#savenote'))
  A.click('#goDress');A.wait_for_timeout(600)
  print('rank shown:',A.inner_text('#dressrank'),'| frigate chip enabled:',A.is_enabled('#dship-frigate'))
  A.click('#dship-frigate');A.click('#sw-h6');A.click('#sw-t3');A.click('#sw-s4');A.click('#sw-c5');A.click('#sw-f1')
  A.click('#em-35');A.wait_for_timeout(300);box=A.locator('#pad').bounding_box();cs=box['width']/16
  for y in range(3,13):
    A.mouse.click(box['x']+(4.5)*cs,box['y']+(y+.5)*cs)
  for x in range(5,8):
    A.mouse.click(box['x']+(x+.5)*cs,box['y']+(3.5)*cs);A.mouse.click(box['x']+(x+.5)*cs,box['y']+(12.5)*cs);A.mouse.click(box['x']+(x+.5)*cs,box['y']+(7.5)*cs)
  A.click('#padflip');A.click('#paduse');A.wait_for_timeout(500)
  wish=EA("paint");print('chosen on main menu:',EA("shipId"),wish['lk'],len(wish['dw']))
  A.click('#dressdone');A.wait_for_timeout(300)
  # set sail: the choice goes to the referee
  A.click('#goOpen');A.wait_for_timeout(500);A.click('#joingo')
  B.click('#goOpen');B.wait_for_timeout(400);B.fill('#guestname','Maria');B.click('#joinguest')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  A.wait_for_timeout(4000)
  sv=A.evaluate("window.__fakeTree().saves.google_gary")
  print('referee save now:',sv['ship'],sv.get('paint',{}).get('lk'),len(sv.get('paint',{}).get('dw','')),'| requests:',[l for l in A.evaluate('window.__refLog') if l[0]=='req'])
  print('A sailing:',EA("[shipId,paint.lk]"),'| A tells others:',EA("netPaint().lk"))
  EA("P.x=60;P.z=40;P.a=0;P.v=0");EB("P.x=60;P.z=24;P.a=Math.PI;P.v=0");A.wait_for_timeout(3000)
  print('B sees A:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>[r.pr.n,SHIPS[r.pr.sh|0].name,r.pr.lk,(r.pr.dw||'').length])"))
  EB("showcase=false");B.wait_for_timeout(500);B.screenshot(path=D+'c_online_B_sees_A.png')
  # B hides other captains' drawings: A's ship is rebuilt with a plain emblem
  EB("hideDraw=true;NET.last=null");B.wait_for_timeout(1500)
  print('B hides drawings, A rebuilt as:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>r.lkKey.slice(-1))"))
  # a cheat tries to show colours the referee never approved
  rec=A.evaluate("window.__fakeTree().players.google_gary");print('A presence lk/dw:',rec.get('lk'),len(rec.get('dw','')))
  # in harbour: repaint, the referee confirms
  EA("P.x=21;P.z=0;P.v=0");A.wait_for_timeout(800);EA("openShop()");A.wait_for_timeout(300);A.click('#tabPaint');A.wait_for_timeout(1200)
  A.screenshot(path=D+'c_online_harbour.png')
  A.click('#em-9');A.click('#sw-s1');A.click('#dressdone');A.wait_for_timeout(3000)
  sv=A.evaluate("window.__fakeTree().saves.google_gary");print('after harbour repaint, referee has:',sv['paint'],'| A:',EA("paint.lk"),'| others see:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>r.pr.lk)"))
  print('errors',errs);b.close()
