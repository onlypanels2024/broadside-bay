# Video rewards, between-battle ads and No ads, with stand-in ads (window.__fakeAds) and the local referee.
import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
ok=True
def check(name,cond):
  global ok;print(('PASS ' if cond else 'FAIL ')+name);ok=ok and bool(cond)
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  ctx.add_init_script("window.__fakeAds={}")
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear();localStorage.setItem('bb-tut','1')");A.reload();A.wait_for_timeout(2500)
  check('start screen offers Remove ads',A.is_visible('#startnoads') and 'Remove ads' in A.inner_text('#startnoads'))
  # Wave battle: the harbour offers two videos per battle
  A.click('#goWaves');A.wait_for_function("__t.state==='play'",timeout=120000);E("wave=3;openShop()");A.wait_for_timeout(500)
  check('harbour shows the video button',A.is_visible('#adgoldbtn'));print('  ',A.inner_text('#adgoldbtn'))
  A.screenshot(path=D+'ad_shop.png')
  g0=E("gold");A.click('#adgoldbtn');A.wait_for_timeout(500);g1=E("gold")
  check('video pays wave gold (125 on wave 3)',g1-g0==125)
  A.click('#adgoldbtn');A.wait_for_timeout(500)
  check('only two videos per battle',A.is_hidden('#adgoldbtn') and E("gold")-g0==250)
  # between battles: none in the first 3 battles, then one, then not again within 4 minutes
  E("$('shopov').hidden=true;state='play';AD.runs=0;AD.last=0;localStorage.removeItem('bb-adlast')")
  inter=lambda:A.evaluate("window.__fakeAds.inter|0")
  for k in range(3):
    E("P.hp=0;gameOver()");A.wait_for_selector('#over:not([hidden])',timeout=20000);A.click('#again');A.wait_for_timeout(600)
  check('no ad in the first three battles',inter()==0)
  E("P.hp=0;gameOver()");A.wait_for_selector('#over:not([hidden])',timeout=20000);A.click('#again');A.wait_for_timeout(600)
  check('ad after the fourth battle',inter()==1)
  E("P.hp=0;gameOver()");A.wait_for_selector('#over:not([hidden])',timeout=20000);A.click('#again');A.wait_for_timeout(600)
  check('not again within four minutes',inter()==1)
  E("AD.last=0;window.__fakeAds.noAds=true");E("P.hp=0;gameOver()");A.wait_for_selector('#over:not([hidden])',timeout=20000);A.click('#again');A.wait_for_timeout(600)
  check('No ads: no ad between battles',inter()==1)
  E("wave=1;AD.waveVids=0;openShop()");A.wait_for_timeout(300);r0=A.evaluate("window.__fakeAds.rewarded|0")
  check('No ads: the bonus needs no video',A.inner_text('#adgoldbtn').lower().startswith('bonus gold'));A.click('#adgoldbtn');A.wait_for_timeout(300)
  check('No ads: no video was shown',A.evaluate("window.__fakeAds.rewarded|0")==r0)
  E("window.__fakeAds.noAds=false;$('shopov').hidden=true;toMenu()");A.wait_for_timeout(500)
  # online: the referee pays the video gold (5 a day) and doubles today's chest once
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:100,earned:0,sunk:0,xp:800,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:Math.floor(Date.now()/86400000)-1,st:3}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()')
  A.wait_for_function("!document.getElementById('dailyov').hidden",timeout=20000)
  check('chest not yet opened: no double button',A.is_hidden('#chest2btn'))
  A.click('#chestbtn');A.wait_for_timeout(2500)
  check('after opening: double button',A.is_visible('#chest2btn'));print('  ',A.inner_text('#chest2btn'))
  A.screenshot(path=D+'ad_chest.png')
  s0=A.evaluate("window.__fakeTree().saves.google_gary.gold");A.click('#chest2btn');A.wait_for_timeout(2500)
  s1=A.evaluate("window.__fakeTree().saves.google_gary.gold")
  check('referee paid the chest again (day 4: '+str(s1-s0)+')',s1-s0>0 and A.is_hidden('#chest2btn'))
  A.click('#dailyclose');A.wait_for_timeout(400)
  E("openShop()");A.wait_for_timeout(500)
  check('harbour video online says 5 left today','5 left today' in A.inner_text('#adgoldbtn').lower())
  for k in range(5):A.click('#adgoldbtn');A.wait_for_timeout(1200)
  s2=A.evaluate("window.__fakeTree().saves.google_gary.gold")
  check('referee paid 5 videos x 100',s2-s1==500)
  check('then no more today',A.is_hidden('#adgoldbtn'))
  A.screenshot(path=D+'ad_online_shop.png')
  check('no page errors',not errs);print(errs[:3])
  b.close()
print('ALL PASS' if ok else 'SOME FAILED')
