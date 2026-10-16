# Ship Designer (developer tools): hidden unlock (7 taps on the title), every option rebuilds the ship, save/load,
# design code, and Done brings back the real ship.
import json,os
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
  print('no locks or stars:',A.locator('.dopt.locked,.dopt.prem,.sw.locked,.sw.prem').count()==0)
  def pick(pairs):
    for k,v in pairs:A.click(f'#do-{k}-{v}');A.wait_for_timeout(120)
  def sw(label,i):A.locator(f'.dsec:has(> .lbl:text-is("{label}")) .swrow .sw').nth(i).click();A.wait_for_timeout(120)
  # a dark pirate ship from classic parts
  A.fill('#dname','Midnight Wraith')
  pick([('size','1_4'),('masts','3'),('tiers','3'),('castle','1_6'),('gallery','1'),('cond','2'),('fig','5'),('emb','2'),('lamps','1')])
  sw('Hull',3);sw('Sails',4);sw('Flag',1);sw('Trim',5)
  A.wait_for_timeout(1500);A.screenshot(path=O+'d_dark_pirate.png')
  A.click('#dsave');A.wait_for_timeout(300);print('msg:',A.inner_text('#dmsg'))
  # a cross-breed: classic hull with modern steam parts
  A.fill('#dname','Iron Corsair')
  pick([('cond','0'),('gallery','0'),('hullMat','iron'),('mastMat','steel'),('sailStyle','junk'),('masts','2'),('tiers','2'),('funnels','1'),('paddles','1'),('bridge','1'),('turrets','2'),('searchlight','1'),('radar','1'),('armour','1'),('fig','0')])
  sw('Hull',4);sw('Funnel colour',1)
  A.wait_for_timeout(2500);A.screenshot(path=O+'d_crossbreed.png')
  # a full steamship: no sails
  pick([('sailStyle','none'),('funnels','2'),('hullMat','steel'),('masts','1')])
  A.wait_for_timeout(2500);A.screenshot(path=O+'d_steamship.png')
  A.click('#dshare');A.wait_for_timeout(500);code=A.inner_text('#dcode');print('code ok:',code.startswith('BBSHIP1:'),len(code))
  A.click('#dsaved button:has-text("Load")');A.wait_for_timeout(800);print('loaded name:',A.input_value('#dname'),'design:',E("JSON.stringify({m:dsg.masts,c:dsg.cond,h:dsg.hullMat})"))
  A.click('#designdone');A.wait_for_timeout(800);print('back on menu:',A.is_visible('#start'),'ship:',E("shipId"),'designOn:',E("designOn"))
  A.reload();A.wait_for_timeout(2000);print('still unlocked after reload:',A.is_visible('#goDesign'))
  print('errors',errs)
  b.close()
