import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})");EB=lambda c:B.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);B.goto(U+'?who=maria');B.wait_for_timeout(2500)
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  B.click('#goOpen');B.wait_for_timeout(400);B.fill('#guestname','Maria');B.click('#joinguest')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  # A becomes a Captain sailing a Frigate with side cannons
  # the referee records Gary as a Captain owning a Frigate with side cannons (in the real game he'd have earned it)
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:0,earned:0,sunk:0,xp:3200,up:{hull:0,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true,frigate:true},ship:'frigate'})")
  A.wait_for_function("__t.ev('shipId')==='frigate'",timeout=20000)
  EA("P.x=60;P.z=40;P.a=0;P.v=0");EB("P.x=60;P.z=22;P.a=0;P.v=0")
  A.wait_for_timeout(3000)
  print('B sees A as ship class:',EB("[...NET.peers.values()].filter(r=>r.ship).map(r=>[r.pr.n,SHIPS[r.pr.sh|0].name,r.pr.mx])"))
  rec=A.evaluate("window.__fakeTree().players")
  json.dump(rec,open('/tmp/players.json','w'))
  B.screenshot(path='tests/browser/p_online_B.png')
  hp0=EB("P.hp");xp0=EA("xp")
  for i in range(10):
    EA("P.x=60;P.z=40;P.a=0;P.v=0;P.cool=0;setAim('side')");EB("P.x=60;P.z=22;P.v=0;P.inv=0")
    A.keyboard.down('Space');A.wait_for_timeout(100);A.keyboard.up('Space');A.wait_for_timeout(1300)
    if EB("state")=='over':break
  A.wait_for_timeout(3000)
  log=A.evaluate('window.__refLog')
  print('B hp',hp0,'->',EB("P.hp"),'| B state',EB("state"))
  print('referee:',sum(1 for l in log if l[0]=='hit' and l[1]),'hits approved,',[l for l in log if l[0]=='hit' and not l[1]][:3],'refused | death credited:',[l for l in log if l[0]=='death'])
  print('A gold',EA("gold"),'| A xp',xp0,'->',EA("xp"))
  A.screenshot(path='tests/browser/p_online_A.png')
  print('errors',errs);b.close()
