import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  A.evaluate("""(()=>{const wk=Math.floor((Date.now()/86400000+3)/7),db=window.__fakeDb;
    db.ref('fleets/fW').set({n:'Sea Wolves',tag:'WOLF',col:1,em:2,own:'google_gary',m:{google_gary:'Gary'}});db.ref('fleets/fK').set({n:'Kings Navy',tag:'KING',col:4,em:11,own:'x',m:{x:'Bob'}});
    db.ref('board/p'+(wk-1)+'/0/fW').set({n:'Sea Wolves',tag:'WOLF',s:40});db.ref('board/p'+(wk-1)+'/0/fK').set({n:'Kings Navy',tag:'KING',s:12});db.ref('board/p'+(wk-1)+'/1/fK').set({n:'Kings Navy',tag:'KING',s:30});
    db.ref('board/p'+wk+'/0/fK').set({n:'Kings Navy',tag:'KING',s:9});
    db.ref('saves/google_gary').set({gold:0,earned:0,sunk:0,xp:300,fleet:'fW',up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:Math.floor(Date.now()/86400000),st:1}});})()""")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()');A.wait_for_timeout(3000)
  print('holders:',E("portData()&&portData().hold"),'| suffix port 0:',E("portSuffix(0)"),'| port 1:',E("portSuffix(1)"))
  g0=A.evaluate("window.__fakeTree().saves.google_gary.gold")
  E("P.x=50;P.z=10");A.wait_for_timeout(600);E("econKill('sloop')");A.wait_for_timeout(2500)
  sv=A.evaluate("window.__fakeTree().saves.google_gary");print('kill near my port: referee gold',g0,'->',sv['gold'])
  E("loadPorts()");A.wait_for_timeout(1500);print('this week at Port Solace:',E("portData().race[0].map(r=>[r.tag,r.s])"))
  A.screenshot(path=D+'p_map.png')
  E("openMenu()");A.wait_for_timeout(200);A.click('#menufleet');A.wait_for_timeout(600);A.screenshot(path=D+'p_fleet_ports.png',full_page=True)
  print('errors',errs);b.close()
