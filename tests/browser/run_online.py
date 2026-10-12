import sys
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
  ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);B.goto(U+'?who=maria');B.wait_for_timeout(2500)
  # A: Google
  A.click('#goOpen');A.wait_for_timeout(500);A.screenshot(path='tests/browser/s_join.png')
  A.click('#joingoogle');A.wait_for_timeout(800);print('A signed-in panel:',A.is_visible('#joinsigned'),A.inner_text('#joinname'))
  A.screenshot(path='tests/browser/s_join_signed.png')
  A.click('#joingo')
  # B: guest
  B.click('#goOpen');B.wait_for_timeout(500);B.fill('#guestname','Maria');B.click('#joinguest')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000)
  for pg in(A,B):pg.evaluate('__t.noAI()')
  A.evaluate("__t.P.x=60;__t.P.z=40;__t.P.a=-Math.PI/2;__t.P.v=0");B.evaluate("__t.P.x=60;__t.P.z=24;__t.P.a=Math.PI;__t.P.v=0")
  A.wait_for_timeout(3000)
  print('A sees:',A.evaluate("[...__t.NET.peers.values()].filter(r=>r.ship).map(r=>r.pr.n)"),'|',A.inner_text('#onlinetxt'))
  print('B sees:',B.evaluate("[...__t.NET.peers.values()].filter(r=>r.ship).map(r=>r.pr.n)"),'|',B.inner_text('#onlinetxt'))
  A.screenshot(path='tests/browser/s_A.png')
  hp0=B.evaluate('__t.P.hp')
  for i in range(10):
    A.evaluate("__t.P.x=60;__t.P.z=40;__t.P.a=-Math.PI/2;__t.P.v=0;__t.P.cool=0");B.evaluate("__t.P.x=60;__t.P.z=24;__t.P.v=0;__t.P.inv=0")
    A.evaluate('__t.shoot()');A.wait_for_timeout(1300)
    if B.evaluate("__t.state")=='over':break
  print('B hp',hp0,'->',B.evaluate('__t.P.hp'),'| B state',B.evaluate('__t.state'))
  A.wait_for_timeout(3000)
  print('referee log:',A.evaluate('window.__refLog'))
  print('A kills',A.evaluate('__t.NET.kills'),'A gold',A.evaluate('__t.gold'))
  tree=A.evaluate('window.__fakeTree()')
  print('cloud save for Google player:',tree.get('saves'))
  print('B (guest) save exists:',any(k.startswith('anon') for k in (tree.get('saves') or {})))
  A.screenshot(path='tests/browser/s_A_kill.png');B.screenshot(path='tests/browser/s_B_sunk.png')
  print('errors',errs);b.close()
