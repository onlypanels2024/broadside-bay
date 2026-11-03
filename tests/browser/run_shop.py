# The shop (Founder's Pack, Season Pass, Lifetime No ads) and the new videos (revive, repair at sea, free chest).
import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  day="Math.floor(Date.now()/86400000)"
  A.evaluate("window.__fakeAds={};window.__fakeShop={};window.__fakeDb.ref('saves/google_gary').set({gold:900,earned:1200,sunk:30,xp:2500,ks:{sloop:30},daily:{d:"+day+",st:1}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()');A.wait_for_timeout(1500)
  sv=lambda:A.evaluate("window.__fakeTree().saves.google_gary")
  EA("openMenu()");A.wait_for_timeout(200)
  print('shop button shown:',A.is_visible('#menushop'))
  A.click('#menushop');A.wait_for_timeout(500);A.screenshot(path=D+'sp_shop.png',full_page=True)
  # Founder's Pack
  A.locator('#storebody button',has_text='Become a Founder').click();A.wait_for_timeout(2500)
  s=sv();print('founder: own',s.get('own'),'gold',s.get('gold'),'| msg:',A.inner_text('#storemsg'))
  A.screenshot(path=D+'sp_founder.png',full_page=True)
  # Season Pass: earn some season XP by sinking ships (the referee counts it)
  EA("P.x=80;P.z=60;P.v=0");A.wait_for_timeout(1500)
  for i in range(5):EA("econRequest({k:'kill',e:'galleon'})");A.wait_for_timeout(150)
  A.wait_for_timeout(2000);A.evaluate("window.__fakeDb.ref('saves/google_gary/px/x').set(1350)")
  A.wait_for_timeout(2500);s=sv();print('season xp',s.get('px'))
  A.locator('#pr-f0').click();A.wait_for_timeout(1500);print('free step 1:',sv().get('pc'))
  A.locator('#pr-p1').click();A.wait_for_timeout(300);print('locked pass tap:',A.inner_text('#storemsg'))
  A.locator('#storebody button',has_text='Get the Season Pass').click();A.wait_for_timeout(2500)
  print('passes',sv().get('pp'))
  for t in ['p0','p1','f1']:
    A.locator('#pr-'+t).click();A.wait_for_timeout(1200)
  s=sv();print('after claims: own',s.get('own'),'pc',s.get('pc'),'gold',s.get('gold'))
  A.screenshot(path=D+'sp_pass.png',full_page=True)
  # Lifetime No ads
  A.locator('#storebody button',has_text='No ads for life').click();A.wait_for_timeout(2500)
  s=sv();print('lifetime: na year',A.evaluate("new Date(%d).getFullYear()"%s.get('na',0)),'noAdsOn',EA("noAdsOn()"))
  A.screenshot(path=D+'sp_lifetime.png',full_page=True)
  # a token can't be used twice
  EA("FB.request({k:'buy',id:'founder',tok:window.__fakeShop&&'x'})");A.wait_for_timeout(800)
  # Esc closes the shop
  A.keyboard.press('Escape');A.wait_for_timeout(300);print('Esc closed shop:',A.is_hidden('#storeov'),'menu open:',A.is_visible('#menuov'))
  # Captain's log: the Founder title and looks
  A.click('#menulog');A.wait_for_timeout(500);print('log open',A.is_visible('#logov'),A.evaluate("[...document.querySelectorAll('.overlay:not([hidden])')].map(o=>o.id)"));print('titles:',A.locator('#logtitles .tchip').all_inner_texts())
  A.locator('#logtitles .tchip',has_text='Founder').click();A.wait_for_timeout(300)
  A.click('#cos-trail6');A.wait_for_timeout(200);A.click('#cos-ball4');A.wait_for_timeout(1500)
  print('referee: title',sv().get('title'),'looks',sv().get('cx'))
  A.screenshot(path=D+'sp_log.png',full_page=True)
  A.keyboard.press('Escape');A.wait_for_timeout(200);A.keyboard.press('Escape');A.wait_for_timeout(300);print('Esc back to sea:',EA("state"),A.is_hidden('#menuov'))
  EA("P.v=12;P.a=0");A.wait_for_timeout(2500);A.screenshot(path=D+'sp_wake.png')
  EA("firing=true");A.wait_for_timeout(350);EA("firing=false");A.wait_for_timeout(100);A.screenshot(path=D+'sp_shot.png')
  # repair video at sea (lifetime No ads: no video, still works); turn No ads off to see the video button
  A.evaluate("window.__fakeAds={noAds:false}")
  EA("P.v=0;P.x=80;P.z=60;P.hp=1;updHud()");A.wait_for_timeout(1500)
  print('repair button:',A.is_visible('#fixbtn'),A.inner_text('#fixbtn') if A.is_visible('#fixbtn') else '')
  A.screenshot(path=D+'sp_fix.png')
  A.click('#fixbtn');A.wait_for_timeout(1500);print('hull after repair',EA("P.hp+'/'+maxHp()"),'button hidden',A.is_hidden('#fixbtn'),'af set',bool(sv().get('af')))
  EA("P.hp=1;updHud()");A.wait_for_timeout(1200);print('second repair offered too soon?',A.is_visible('#fixbtn'))
  # free chest every 4 hours
  EA("openDaily('sea')");A.wait_for_timeout(500);print('free chest:',A.inner_text('#chest3btn'))
  A.click('#chest3btn');A.wait_for_timeout(1800);print('after:',A.inner_text('#chest3btn'),'| ac set',bool(sv().get('ac')))
  A.screenshot(path=D+'sp_chest.png',full_page=True)
  print('referee log:',[r for r in A.evaluate("window.__refLog") if r[1] in ('buy','pass','adfix','adchest','title','cos')])
  # revive once in a Wave battle
  A.click("#dailyclose");A.wait_for_timeout(300);EA("toMenu()");A.wait_for_timeout(500);A.click("#goWaves");A.wait_for_function("__t.state==='play'",timeout=30000);A.wait_for_timeout(800)
  EA("P.hp=0;gameOver()");A.wait_for_timeout(1800);print('revive offered:',A.is_visible('#revivebtn'),A.inner_text('#revivebtn'))
  A.screenshot(path=D+'sp_revive.png')
  A.click('#revivebtn');A.wait_for_timeout(1200);print('after revive: state',EA("state"),'hull',EA("P.hp+'/'+maxHp()"),'ship shown',EA("pship.visible"))
  A.screenshot(path=D+'sp_revived.png')
  EA("P.hp=0;gameOver()");A.wait_for_timeout(1800);print('second revive offered?',A.is_visible('#revivebtn'))
  print('errors',errs);b.close()
