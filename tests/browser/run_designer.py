# Ship Designer: hidden unlock (7 taps on the title), options rebuild the ship, save/load, design code, and Done restores the real ship.
import json,os,sys
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html';O=os.environ.get('OUT','tests/browser/')
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
  A=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2).new_page();errs=[]
  A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary');A.wait_for_timeout(1500);A.evaluate("localStorage.setItem('bb-tut','1')");A.reload();A.wait_for_timeout(2500)
  sh=E("(()=>{const t0=Date.now();for(let k=0;k<8000;k++){const t=t0+k*15000;const w=weatherAt(t);if(w.day>.95&&w.cloud<.05)return k*15000;}return 0;})()")
  E(f"window.__wxShift={sh};0")
  print('hidden before:',A.is_hidden('#goDesign'))
  A.evaluate("for(let i=0;i<7;i++)document.querySelector('#start h1').click()");A.wait_for_timeout(300)
  print('visible after 7 taps:',A.is_visible('#goDesign'))
  A.click('#goDesign');A.wait_for_timeout(1200)
  A.screenshot(path=O+'d_designer_default.png')
  A.fill('#dname','Black Widow')
  for k,v in [('size','1_4'),('masts','3'),('tiers','3'),('castle','1_6'),('fore','1'),('guns','5'),('decks','2'),('fig','2'),('pet','1')]:
    A.click(f'#do-{k}-{v}');A.wait_for_timeout(150)
  A.locator('.dsec:has-text("Hull") .swrow .sw').nth(3).click()
  A.locator('.dsec:has-text("Sails") .swrow .sw').nth(4).click()
  A.locator('.dsec:has-text("Sail stripe") .swrow .sw').nth(2).click()
  A.wait_for_timeout(1500);A.screenshot(path=O+'d_designer_custom.png')
  A.click('#dsave');A.wait_for_timeout(300);print('msg:',A.inner_text('#dmsg'))
  A.click('#drandom');A.wait_for_timeout(1500);A.screenshot(path=O+'d_designer_random.png')
  A.click('#dshare');A.wait_for_timeout(500);code=A.inner_text('#dcode');print('code ok:',code.startswith('BBSHIP1:'),len(code))
  A.click('#dsaved button:has-text("Load")');A.wait_for_timeout(800);print('loaded name:',A.input_value('#dname'))
  print('design:',E("JSON.stringify({m:dsg.masts,g:dsg.guns,s:dsg.size})"))
  A.click('#designdone');A.wait_for_timeout(800);print('back on menu:',A.is_visible('#start'),'ship:',E("shipId"),'designOn:',E("designOn"))
  A.reload();A.wait_for_timeout(2000);print('still unlocked after reload:',A.is_visible('#goDesign'))
  print('errors',errs)
  b.close()
