import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  # some rivals already on this week's board
  A.evaluate("""(()=>{const wk=Math.floor((Date.now()/86400000+3)/7);const names=['Blackbeard','Anne Bonny','Calico Jack','Mary Read','Henry Morgan','Ching Shih','Bart Roberts','Stede Bonnet'];
    names.forEach((n,i)=>{window.__fakeDb.ref('board/w'+wk+'/r'+i).set({n,s:(i*3+1)%17+2,g:((i*7)%9+1)*210,c:i%4});window.__fakeDb.ref('board/all/r'+i).set({n,xp:[9500,6000,3500,1600,800,300,120,20][i],s:40-i*4});});})()""")
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:0,earned:0,sunk:0,xp:3200,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:Math.floor(Date.now()/86400000),st:1}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()')
  for k in range(6):
    E("P.x=90;P.z=70");A.wait_for_timeout(300);E("econKill('sloop')");A.wait_for_timeout(500)
  A.wait_for_timeout(2500)
  E("openMenu()");A.wait_for_timeout(200);print('menu has leaderboards:',A.is_visible('#menuboard'));A.click('#menuboard');A.wait_for_timeout(1500)
  print('week, ships sunk:',[r.split('\n') for r in A.locator('#blist .brow').all_inner_texts()][:10])
  A.screenshot(path=D+'b_week.png')
  A.click('#bG');A.wait_for_timeout(800);print('gold top 3:',A.locator('#blist .brow').all_inner_texts()[:3])
  A.click('#bAll');A.wait_for_timeout(800);print('all time:',A.locator('#blist .brow').all_inner_texts()[:6]);A.screenshot(path=D+'b_all.png')
  A.click('#boardclose');print('back to menu:',A.is_visible('#menuov'))
  print('errors',errs);b.close()
