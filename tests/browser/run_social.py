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
  for who in ['gary','maria']:A.evaluate("window.__fakeDb.ref('saves/google_"+who+"').set({gold:0,earned:0,sunk:0,xp:300,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:"+day+",st:1}})")
  for pg in(A,B):pg.click('#goOpen');pg.wait_for_timeout(400);pg.click('#joingoogle');pg.wait_for_timeout(600);pg.click('#joingo')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  EA("P.x=60;P.z=40;P.a=0;P.v=0");EB("P.x=60;P.z=24;P.a=0;P.v=0");A.wait_for_timeout(3000)
  # Maria adds Gary
  EB("openMenu()");B.wait_for_timeout(200);B.click('#menufriends');B.wait_for_timeout(500);B.screenshot(path=D+'s_friends_add.png')
  B.locator('#friendbody .shipbtn',has_text='Add friend').first.click();B.wait_for_timeout(1500);print('B:',B.inner_text('#friendmsg'))
  B.click('#friendclose');EB("closeMenu()")
  # Gary accepts
  A.wait_for_timeout(1000);EA("openMenu()");A.wait_for_timeout(200);A.click('#menufriends');A.wait_for_timeout(500);A.screenshot(path=D+'s_friends_req.png')
  A.locator('#friendbody .shipbtn',has_text='Accept').click();A.wait_for_timeout(1500)
  print('A friends:',EA("friendsData().list"),'| B friends:',EB("friendsData().list"))
  A.screenshot(path=D+'s_friends_list.png');A.click('#friendclose');EA("closeMenu()")
  # quick chat
  A.click('#chatbtn');A.wait_for_timeout(300);A.screenshot(path=D+'s_chat_menu.png');A.click('#chat-0');A.wait_for_timeout(3000)
  print('B chat log:',B.locator('#chatlog div').all_inner_texts(),'| bubble:',EB("[...NET.peers.values()].map(r=>r.say)"))
  B.screenshot(path=D+'s_chat_seen.png')
  print('A on B chart is friend:',EB("[...NET.peers.values()].map(r=>isFriend(r.by||r.peer))"))
  A.click('#chatbtn');A.click('#chat-1');A.click('#chatbtn');A.click('#chat-2');A.wait_for_timeout(300);print('spam guard:',A.locator('#chatlog div').all_inner_texts()[-1])
  print('errors',errs);b.close()
