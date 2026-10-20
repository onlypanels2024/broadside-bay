# The Ironfang shark: surfaces in a shark window, hunts (warning then a 2-damage bite), shares its health, and pays once killed.
import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':360,'height':640},device_scale_factor=2)
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:0,earned:0,sunk:0,xp:9500,up:{hull:3,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true,frigate:true},ship:'frigate',daily:{d:Math.floor(Date.now()/86400000),st:1}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()');A.wait_for_timeout(1000)
  # jump to the start of a shark window (and away from the kraken)
  E("(()=>{const n=Date.now();let s=Math.ceil(n/SH.slot);for(let k=0;k<5000;k++,s++){if(!sharkRises(s))continue;const w=weatherAt(s*SH.slot+40000);if(w.day>.95&&w.cloud<.03&&w.rain<.01)break;}window.__wxShift=s*SH.slot+40000-n;})();0")
  A.wait_for_function("__t.ev('shark.on')",timeout=120000);A.wait_for_timeout(200);A.screenshot(path=D+'sh_note.png');print('note:',E("$('hudnote').textContent"),E("(()=>{const n=$('hudnote'),r=n.getBoundingClientRect();return [n.hidden,n.className,getComputedStyle(n).display,getComputedStyle(n).opacity,Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height),n.parentElement.id,n.parentElement.hidden]})()"));A.wait_for_timeout(2300)
  print('shark up:',E("[shark.on,shark.slot,shark.hp,Math.round(shark.cx),Math.round(shark.cz),sharkRises(shark.slot)]"))
  E("P.x=shark.x+26;P.z=shark.z+8;P.a=Math.PI;P.v=0;P.inv=0;shark.atkT=.2;0");A.wait_for_timeout(600)
  hp0=E("P.hp");print('mode after closing in:',E("shark.mode"))
  A.wait_for_timeout(700);A.screenshot(path=D+'sh_warn.png')
  E("shark.mt=.05;0")
  for i in range(60):
    m=E("shark.mode")
    if m=='lunge' and i%4==0:A.screenshot(path=D+'sh_lunge.png')
    if m in('dive','swim') and i>2:break
    A.wait_for_timeout(500)
  A.wait_for_timeout(300)
  print('hull before/after a bite:',hp0,E("P.hp"),'| bitten:',E("shark.bite"))
  E("P.hp=P.max||9;P.inv=1e9;0")
  print('boss bar:',A.is_visible('#boss'),A.inner_text('#bossname'))
  A.screenshot(path=D+'sh_play.png')
  slot=E("shark.slot")
  A.evaluate(f"window.__fakeDb.ref('shark/{slot}').set({{hp:4,hits:{{google_gary:0}}}})");A.wait_for_timeout(500)
  for i in range(4):E("sharkHurt({x:shark.x,z:shark.z});0");A.wait_for_timeout(300)
  A.wait_for_timeout(3000)
  log=[l for l in A.evaluate('window.__refLog') if l[0]=='req' and l[2]=='shark']
  print('shared shark now:',A.evaluate(f"window.__fakeTree().shark['{slot}']"),'| dead',E("shark.dead"),'| claim:',log,'| gold',E("gold"))
  A.screenshot(path=D+'sh_dead.png')
  print('errors',errs[:5]);b.close()
