import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");A.reload();A.wait_for_timeout(2500)
  A.screenshot(path=D+'st_start.png',full_page=True)
  A.click('#goStory');A.wait_for_timeout(400);A.screenshot(path=D+'st_list.png')
  print('chapters enabled:',E("[...document.querySelectorAll('#storylist .chap')].map(b=>!b.disabled)"))
  A.click('#chap-0');A.wait_for_timeout(200);A.screenshot(path=D+'st_brief.png');A.click('#storygo')
  A.wait_for_function("__t.state==='play'",timeout=60000);A.wait_for_timeout(5000)
  print('m1:',A.inner_text('#objective'),'| foes',E("enemies.length"));A.screenshot(path=D+'st_m1.png')
  # merchant reaches port
  E("story.guard.x=PORTS[1].x+20;story.guard.z=PORTS[1].z");A.wait_for_function("!document.getElementById('storyov').hidden",timeout=60000)
  print('m1 end:',A.inner_text('#storyeye'),'|',A.inner_text('#storytxt'));A.screenshot(path=D+'st_win.png')
  print('wave hold gold:',A.evaluate("JSON.parse(localStorage.getItem('bb-waves-v1')).gold"))
  A.click('#storygo');A.wait_for_timeout(200);A.click('#storygo');A.wait_for_function("__t.state==='play'",timeout=60000);A.wait_for_timeout(4000)
  print('m2:',A.inner_text('#objective'))
  E("story.kills=8");A.wait_for_function("!document.getElementById('storyov').hidden",timeout=60000);print('m2 end:',A.inner_text('#storyeye'))
  A.click('#storygo');A.wait_for_timeout(200);A.click('#storygo');A.wait_for_function("__t.state==='play'",timeout=60000);A.wait_for_timeout(4000)
  print('m3:',A.inner_text('#objective'),'| guards',E("enemies.length"));A.screenshot(path=D+'st_m3.png')
  E("enemies.forEach(e=>e.cool=99);P.x=treasure.isl.x+treasure.isl.r*1.3+4;P.z=treasure.isl.z;P.v=0;P.inv=999");A.wait_for_timeout(800);A.click('#dig')
  A.wait_for_function("!document.getElementById('storyov').hidden",timeout=90000);print('m3 end:',A.inner_text('#storyeye'))
  A.click('#storygo');A.wait_for_timeout(200);A.click('#storygo');A.wait_for_function("__t.state==='play'",timeout=60000);A.wait_for_timeout(4000)
  print('m4:',A.inner_text('#objective'),A.inner_text('#bossname'));A.screenshot(path=D+'st_m4.png')
  # lose mission 4 on purpose
  E("P.inv=0;P.hp=1;hurtPlayer()");A.wait_for_function("!document.getElementById('storyov').hidden",timeout=60000);print('m4 lost:',A.inner_text('#storyeye'),'|',A.inner_text('#storytxt'),'| button',A.inner_text('#storygo'))
  A.click('#storygo');A.wait_for_function("__t.state==='play'",timeout=60000);A.wait_for_timeout(3000)
  E("enemies.forEach(e=>e.hp=0)");A.wait_for_function("!document.getElementById('storyov').hidden",timeout=60000);print('m4 end:',A.inner_text('#storyeye'))
  A.click('#storygo');A.wait_for_timeout(200);A.click('#storygo');A.wait_for_function("__t.state==='play'",timeout=60000)
  A.wait_for_function("__t.ev('kraken.rise')>=1",timeout=90000);E("P.x=kraken.x+18;P.z=kraken.z;P.a=Math.PI;P.inv=999");A.wait_for_timeout(2500)
  print('m5:',A.inner_text('#objective'),'| kraken hp',E("kraken.hp"));A.screenshot(path=D+'st_m5.png')
  E("kraken.hp=0");A.wait_for_function("!document.getElementById('storyov').hidden",timeout=60000);print('m5 end:',A.inner_text('#storyeye'),'|',A.inner_text('#storygo'))
  A.click('#storygo');A.wait_for_timeout(300);print('stars:',E("[...document.querySelectorAll('#storylist .stars')].map(s=>s.textContent)"))
  A.click('#storyback');A.wait_for_timeout(500);print('note:',A.inner_text('#storynote'))
  print('errors',errs);b.close()
