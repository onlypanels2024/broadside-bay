import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})");EB=lambda c:B.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");B.goto(U+'?who=maria');B.wait_for_timeout(2000)
  day="Math.floor(Date.now()/86400000)"
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:500,earned:0,sunk:0,xp:3200,up:{hull:3,sails:0,reload:0,triple:0,broadside:1},ships:{brig:true,frigate:true},ship:'frigate',daily:{d:"+day+",st:1}})")
  A.evaluate("window.__fakeDb.ref('saves/google_maria').set({gold:400,earned:0,sunk:0,xp:300,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:"+day+",st:1}})")
  for pg in(A,B):pg.click('#goOpen');pg.wait_for_timeout(400);pg.click('#joingoogle');pg.wait_for_timeout(600);pg.click('#joingo')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  EA("P.x=60;P.z=40");EB("P.x=60;P.z=24");A.wait_for_timeout(3000)
  EA("openMenu()");A.wait_for_timeout(200);A.click('#menufriends');A.wait_for_timeout(500)
  A.locator('#friendbody .shipbtn',has_text='Duel').first.click();A.wait_for_timeout(300);print('A:',A.inner_text('#friendmsg'))
  A.click('#friendclose');EA("closeMenu()")
  B.wait_for_function("!document.getElementById('duelov').hidden",timeout=20000);print('B sees:',B.inner_text('#dueltxt')[:60]);B.screenshot(path=D+'du_offer.png')
  B.click('#duelyes');A.wait_for_function("__t.ev('!!duel')",timeout=20000)
  print('A in duel:',EA("[duel.name,shipId,maxHp(),Math.round(P.x),Math.round(P.z)]"),'| B:',EB("[duel.name,shipId,maxHp(),Math.round(P.x)]"))
  A.wait_for_timeout(4000);A.screenshot(path=D+'du_arena.png')
  print('presence du:',A.evaluate("[window.__fakeTree().players.google_gary.du,window.__fakeTree().players.google_maria.du]"))
  for i in range(14):
    EA("P.x=ARENA_D.x;P.z=ARENA_D.z+8;P.a=0;P.v=0;P.cool=0;setAim('side')");EB("P.x=ARENA_D.x;P.z=ARENA_D.z-8;P.v=0;P.inv=0")
    A.keyboard.down('Space');A.wait_for_timeout(100);A.keyboard.up('Space');A.wait_for_timeout(1200)
    if EB("state")=='over':break
  A.wait_for_timeout(3500)
  print('B state',EB("state"),'| B overlay:',B.inner_text('#overtxt') if B.is_visible('#over') else '-')
  B.screenshot(path=D+'du_lost.png');A.screenshot(path=D+'du_won.png')
  print('death log:',[l for l in A.evaluate('window.__refLog') if l[0]=='death'])
  sv=A.evaluate("window.__fakeTree().saves");print('gold: Gary',sv['google_gary']['gold'],'duels',sv['google_gary'].get('ks',{}).get('duel'),'| Maria',sv['google_maria']['gold'])
  A.wait_for_timeout(3000);print('A after:',EA("[!!duel,shipId,Math.round(P.x),Math.round(P.z)]"))
  if B.is_visible('#over'):B.click('#again');B.wait_for_timeout(1500)
  print('B after:',EB("[!!duel,shipId,state]"))
  print('errors',errs);b.close()
