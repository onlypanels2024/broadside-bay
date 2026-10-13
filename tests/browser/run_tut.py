import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);A=b.new_page(viewport={'width':400,'height':800})
  errs=[];A.on('pageerror',lambda e:errs.append(str(e)));E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");A.reload();A.wait_for_timeout(2500)
  print('tutorial offered:',A.is_visible('#tutbox'),'| how-to gone:',A.locator('details.how').count()==0);A.screenshot(path=D+'t_start.png')
  A.click('#goTut');A.wait_for_function("__t.state==='play'",timeout=60000);A.wait_for_timeout(1500);print('1:',A.inner_text('#objective'));A.screenshot(path=D+'t_1.png')
  E("P.x+=30");A.wait_for_timeout(1500);print('2:',A.inner_text('#objective'),'| fire glows',E("$('fire').classList.contains('glowpulse')"));A.screenshot(path=D+'t_2.png')
  E("P.a=Math.atan2(story.tg.z-P.z,story.tg.x-P.x)")
  for i in range(10):
    if E("story.step")!=1:break
    A.keyboard.down('Space');A.wait_for_timeout(500);A.keyboard.up('Space');A.wait_for_timeout(2500)
  print('3:',A.inner_text('#objective'));A.click('#aim');A.wait_for_timeout(1200);print('4:',A.inner_text('#objective'))
  E("P.a=Math.atan2(story.tg.z-P.z,story.tg.x-P.x)-Math.PI/2")
  for i in range(10):
    if E("story.step")!=3:break
    A.keyboard.down('Space');A.wait_for_timeout(500);A.keyboard.up('Space');A.wait_for_timeout(2500)
  print('5:',A.inner_text('#objective'))
  for i in range(30):
    if E("story.step")!=4:break
    E("const c=pickups.find(p=>p.k==='coin');if(c){P.x=c.x;P.z=c.z;}");A.wait_for_timeout(400)
  print('6:',A.inner_text('#objective'),'gold',E("gold"))
  E("P.x=PORTS[0].x+18;P.z=PORTS[0].z");A.wait_for_timeout(1500);A.screenshot(path=D+'t_dock.png');A.click('#dock');A.wait_for_timeout(800)
  print('7:',A.inner_text('#objective'));A.screenshot(path=D+'t_shop.png');A.click('#buy-sails');A.wait_for_timeout(300);print('8:',A.inner_text('#objective'))
  A.click('#next');A.wait_for_timeout(600);print('end:',A.inner_text('#storyeye'),'|',A.inner_text('#storytxt')[:90]);A.screenshot(path=D+'t_end.png')
  print('wave hold:',A.evaluate("JSON.parse(localStorage.getItem('bb-waves-v1')).gold"),'| starter flag',A.evaluate("localStorage.getItem('bb-starter')"))
  A.click('#storygo');A.wait_for_timeout(600);print('back: tutbox hidden',not A.is_visible('#tutbox'),'| replay link',A.is_visible('#replayTut'))
  print('errors',errs);b.close()
