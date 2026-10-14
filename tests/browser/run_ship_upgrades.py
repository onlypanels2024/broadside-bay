import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:20000,earned:0,sunk:0,xp:9500,up:{hull:3,sails:3,reload:3,triple:1,broadside:1},ships:{brig:true},ship:'brig'})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()')
  A.wait_for_function("__t.ev('up.hull')===3",timeout=20000)
  print('start:',EA("[shipId,JSON.stringify(up)]"))
  A.evaluate("document.getElementById('dailyov').hidden=true");EA("P.x=PORTS[0].x+21;P.z=PORTS[0].z;P.v=0");A.wait_for_timeout(1500);A.click('#dock');A.wait_for_timeout(1200)
  print('shop note:',A.inner_text('.shopnote'))
  A.click('#tabYard');A.wait_for_timeout(300);A.click('#ship-frigate');A.wait_for_timeout(2500)
  print('bought frigate:',EA("[shipId,JSON.stringify(up),JSON.stringify(shipUps)]"),'| referee:',A.evaluate("JSON.stringify((window.__fakeTree().saves.google_gary||{}).up)"),A.evaluate("JSON.stringify((window.__fakeTree().saves.google_gary||{}).ups)"))
  A.click('#tabUp');A.wait_for_timeout(300);A.screenshot(path='tests/browser/c_ship_upgrades.png')
  A.click('#tabYard');A.wait_for_timeout(300);A.click('#ship-brig');A.wait_for_timeout(2500)
  print('back to brig:',EA("[shipId,JSON.stringify(up)]"),'| referee:',A.evaluate("JSON.stringify((window.__fakeTree().saves.google_gary||{}).up)"))
  print('errors',errs);b.close()
