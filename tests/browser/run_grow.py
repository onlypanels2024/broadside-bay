import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  A.click('#goOpen');A.wait_for_timeout(400);A.fill('#guestname','Gary');A.click('#joinguest');A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()')
  A.wait_for_timeout(1500)
  print('open sea: size',E("WORLD"),'islands',E("islands.length"),'built nearby',E("islands.filter(i=>i.g).length"))
  A.evaluate("window.__fakeDb.ref('world').set({day:Math.floor(Date.now()/86400000),tier:2})");A.wait_for_timeout(1500)
  print('server says tier 2: size',E("WORLD"),'islands',E("islands.length"),'built',E("islands.filter(i=>i.g).length"))
  E("P.x=360;P.z=-360");A.wait_for_timeout(2500);print('sailed to the new edge: built',E("islands.filter(i=>i.g).length"),'| near me',E("islands.filter(i=>Math.hypot(i.x-P.x,i.z-P.z)<230).length"))
  A.screenshot(path=D+'g_edge.png')
  # all phones build the same new islands
  ring=E("islands.slice(-5).map(i=>[Math.round(i.x),Math.round(i.z)])");print('last ring islands',ring)
  E("toMenu()");A.click('#goWaves');A.wait_for_function("__t.state==='play'");A.wait_for_timeout(500)
  sizes=[]
  for w in range(1,9):
    E(f"wave={w-1};nextWave()");sizes.append((E("wave"),E("ARENA"),E("islands.length")))
  print('waves (wave, half-width, islands):',sizes)
  print('errors',errs);b.close()
