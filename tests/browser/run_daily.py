import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();errs=[];A.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()")
  # yesterday's chest was opened (day 3 streak) so today is day 4
  A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:100,earned:0,sunk:0,xp:800,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:Math.floor(Date.now()/86400000)-1,st:3}})")
  A.click('#goOpen');A.wait_for_timeout(400);A.click('#joingoogle');A.wait_for_timeout(600);A.click('#joingo')
  A.wait_for_function("__t.state==='play'",timeout=90000);A.evaluate('__t.noAI()')
  A.wait_for_function("!document.getElementById('dailyov').hidden",timeout=20000)
  print('popup opened by itself:',A.inner_text('#chestbtn'),'|',A.inner_text('#chestnote'))
  A.screenshot(path=D+'d_daily.png')
  g0=E("gold");A.click('#chestbtn');A.wait_for_timeout(2500)
  print('gold',g0,'->',E("gold"),'| referee:',A.evaluate("window.__fakeTree().saves.google_gary.gold"),A.evaluate("window.__fakeTree().saves.google_gary.daily"),'| button:',A.inner_text('#chestbtn'))
  A.click('#dailyclose');A.wait_for_timeout(800)
  print('quest chip:',A.inner_text('#qchip'),'visible',A.is_visible('#qchip'))
  # finish today's quests the honest way: claim kills at sea through the referee (spaced so the rate limiter is happy)
  qs=E("dailyState().quests.map(q=>[q.Q.id,q.Q.n])");print('today:',qs)
  EA=E
  for k in range(8):
    EA("P.x=90;P.z=70;");A.wait_for_timeout(300);EA("econKill('sloop')");A.wait_for_timeout(500)
  EA("econKill('galleon')");A.wait_for_timeout(400);EA("econKill('galleon')");A.wait_for_timeout(3000)
  print('progress:',E("dailyState().quests.map(q=>[q.Q.id,q.p,q.Q.n,q.done])"))
  A.click('#qchip');A.wait_for_timeout(500);A.screenshot(path=D+'d_quests.png')
  done=[q for q in E("dailyState().quests.map(q=>[q.i,q.done,q.claimed])") if q[1] and not q[2]]
  for q in done:
    g0=E("gold");A.click(f'#qclaim-{q[0]}');A.wait_for_timeout(2500);print('claimed quest',q[0],'gold',g0,'->',E("gold"),'| referee gold',A.evaluate("window.__fakeTree().saves.google_gary.gold"))
  print('referee log:',[l for l in A.evaluate('window.__refLog') if l[0]=='req' and l[1] in('daily','quest')])
  A.screenshot(path=D+'d_quests_claimed.png')
  print('errors',errs);b.close()
