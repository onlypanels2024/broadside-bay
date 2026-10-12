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
  A.click('#padflip');hx=EA("padHex()")
  # 1) a swastika is stopped on the phone straight away
  EA("pad.bits.fill(0);for(let k=-4;k<=4;k++){pad.bits[(8+k)*16+8]=1;pad.bits[8*16+8+k]=1;}for(let k=0;k<=4;k++){pad.bits[4*16+8+k]=1;pad.bits[(8+k)*16+12]=1;pad.bits[12*16+8-k]=1;pad.bits[(8-k)*16+4]=1;}padDraw()")
  A.click('#paduse');A.wait_for_timeout(300);print('swastika:',A.inner_text('#padmsg'),'| still drawing:',A.is_visible('#drawov'))
  A.screenshot(path=D+'c_pad_blocked.png')
  # 2) a drawing the AI says is rude is refused by the referee
  EA(f"padFrom('{hx}');padDraw()");A.evaluate(f"window.__rude=['{hx}']")
  A.click('#paduse');A.wait_for_timeout(300);print('while checking:',A.inner_text('#paduse'),'|',A.inner_text('#padmsg'))
  A.wait_for_function("!document.getElementById('paduse').disabled",timeout=30000);print('rude drawing:',A.inner_text('#padmsg'),'| still drawing:',A.is_visible('#drawov'))
  A.screenshot(path=D+'c_pad_rude.png')
  # 3) an ordinary drawing passes
  A.evaluate("window.__rude=[]");A.click('#paduse');A.wait_for_function("document.getElementById('drawov').hidden",timeout=30000);A.wait_for_timeout(500)
  print('ok drawing accepted:',EA("paint.dw")==hx,'| checks:',[l for l in A.evaluate('window.__refLog') if l[0]=='check'])
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
  # B reports A's drawing: hidden for B at once; the referee's second look finds it rude and removes it
  A.evaluate(f"window.__rudeOnReport=['{hx}']")
  EB("hideDraw=false;NET.last=null");B.wait_for_timeout(800);EB("openMenu()");B.wait_for_timeout(200)
  print('report button shown:',B.is_visible('#menureport'));B.click('#menureport');B.wait_for_timeout(300);B.screenshot(path=D+'c_report.png')
  B.click('#replist .shipbtn');B.wait_for_timeout(4000)
  print('report log:',[l for l in A.evaluate('window.__refLog') if l[0]=='report'],'| A paint now:',EA("[paint.lk,paint.dw]"),'| B sees A:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>[r.pr.lk,(r.pr.dw||'').length])"))
  B.click('#repdone');EB("closeMenu()")
  # A can never use that drawing again
  A.evaluate("window.__rudeOnReport=[]");EA("openShop()");A.wait_for_timeout(200);A.click('#tabPaint');A.wait_for_timeout(500);A.click('#em-35');A.wait_for_timeout(300)
  EA(f"padFrom('{hx}');padDraw();okDrawings=[]");A.click('#paduse');A.wait_for_function("!document.getElementById('paduse').disabled",timeout=30000);print('reuse removed drawing:',A.inner_text('#padmsg'))
  A.click('#padcancel');A.click('#dressdone');A.click('#next');A.wait_for_timeout(500)
  # in harbour: repaint, the referee confirms
  EA("P.x=21;P.z=0;P.v=0");A.wait_for_timeout(800);EA("openShop()");A.wait_for_timeout(300);A.click('#tabPaint');A.wait_for_timeout(1200)
  A.screenshot(path=D+'c_online_harbour.png')
  A.click('#em-9');A.click('#sw-s1');A.click('#dressdone');A.wait_for_timeout(3000)
  sv=A.evaluate("window.__fakeTree().saves.google_gary");print('after harbour repaint, referee has:',sv['paint'],'| A:',EA("paint.lk"),'| others see:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>r.pr.lk)"))
  print('errors',errs);b.close()
