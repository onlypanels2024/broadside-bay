import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:0,earned:0,sunk:0,xp:300,up:{hull:3,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true},ship:'brig',daily:{d:Math.floor(Date.now()/86400000),st:1}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()');A.wait_for_timeout(1500)
  log=lambda k:[l for l in A.evaluate('window.__refLog') if l[0]=='req' and l[2]==k]
  # ---- treasure
  E("P.x=60;P.z=40;addPickup('map',P.x+1,P.z)");A.wait_for_timeout(1200)
  print('map picked up:',E("!!treasure"),'island at',E("treasure&&[Math.round(treasure.isl.x),Math.round(treasure.isl.z)]"))
  A.screenshot(path=D+'e_map.png')
  E("P.x=treasure.isl.x+treasure.isl.r*1.3+4;P.z=treasure.isl.z;P.v=0");A.wait_for_timeout(800)
  print('dig button:',A.is_visible('#dig'));A.click('#dig');A.wait_for_timeout(1200);A.screenshot(path=D+'e_dig.png');A.wait_for_function("__t.ev('treasure===null')",timeout=60000)
  A.wait_for_timeout(2000);print('treasure log:',log('treasure'),'gold',E("gold"))
  # ---- convoy: escort it to port
  E("P.x=-60;P.z=-60;P.v=0;convoyT=0");A.wait_for_timeout(800)
  print('convoy:',E("convoy&&[convoy.dest.name,convoy.esc.length,Math.round(Math.hypot(convoy.m.x-P.x,convoy.m.z-P.z))]"))
  E("P.x=convoy.m.x-14;P.z=convoy.m.z+6;P.a=convoy.m.a");A.wait_for_timeout(1500);A.screenshot(path=D+'e_convoy.png')
  E("convoy.total=40;convoy.near=40;convoy.m.x=convoy.dest.x+10;convoy.m.z=convoy.dest.z;P.x=convoy.m.x+20;P.z=convoy.m.z");A.wait_for_timeout(2500)
  print('escort log:',log('escort'),'| convoy now',E("!!convoy"))
  # ---- convoy: sink the merchant
  E("P.x=-80;P.z=80;convoyT=0");A.wait_for_timeout(800);E("P.x=convoy.m.x+12;P.z=convoy.m.z;onEnemyHit(convoy.m);convoy.m.hp=0");A.wait_for_timeout(2500)
  print('merchant log:',log('merchant'),'| escorts now:',E("enemies.filter(e=>e.kind==='galleon').map(e=>e.mode)"))
  E("enemies.forEach(e=>{e.hp=-99;e.silent=true})");A.wait_for_timeout(500)
  # ---- kraken
  sh=E("(()=>{const t0=serverNowMs();for(let k=0;k<200;k++){const t=t0+k*30000,sl=Math.floor(t/480000);if(t-sl*480000<200000&&t-sl*480000>15000)return k*30000;}return 0;})()")
  E(f"window.__wxShift={sh}");A.wait_for_timeout(1500)
  print('kraken up:',E("[kraken.on,kraken.slot,Math.round(kraken.x),Math.round(kraken.z)]"))
  E("P.x=kraken.x+16;P.z=kraken.z;P.a=Math.PI;P.v=0;P.inv=0");A.wait_for_timeout(4000);A.screenshot(path=D+'e_kraken.png')
  print('kraken bar:',A.is_visible('#boss'),A.inner_text('#bossname'))
  slot=E("kraken.slot")
  A.evaluate(f"window.__fakeDb.ref('kraken/{slot}').set({{hp:4,hits:{{google_gary:0}}}})");A.wait_for_timeout(500)
  for i in range(4):E("krakenHurt({x:kraken.x,z:kraken.z})");A.wait_for_timeout(300)
  A.wait_for_timeout(3000)
  print('shared kraken now:',A.evaluate(f"window.__fakeTree().kraken['{slot}']"),'| dead',E("kraken.dead"),'| claim:',log('kraken'))
  A.screenshot(path=D+'e_kraken_dead.png')
  print('referee gold',A.evaluate("window.__fakeTree().saves.google_gary.gold"),'| sunk',A.evaluate("window.__fakeTree().saves.google_gary.sunk"))
  print('errors',errs);b.close()
