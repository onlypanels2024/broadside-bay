import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  A=ctx.new_page();B=ctx.new_page();errs=[]
  for pg,n in((A,'A'),(B,'B')):pg.on('pageerror',lambda e,n=n:errs.append(n+':'+str(e)))
  EA=lambda c:A.evaluate(f"__t.ev({json.dumps(c)})");EB=lambda c:B.evaluate(f"__t.ev({json.dumps(c)})")
  A.goto(U+'?who=gary&referee=1');A.wait_for_timeout(1500);A.evaluate("localStorage.clear()");B.goto(U+'?who=maria');B.wait_for_timeout(2000);B.evaluate("localStorage.clear()")
  day="Math.floor(Date.now()/86400000)"
  for who in ['gary','maria']:A.evaluate("window.__fakeDb.ref('saves/google_"+who+"').set({gold:0,earned:0,sunk:0,xp:300,up:{hull:0,sails:0,reload:0,triple:0,broadside:0},ships:{brig:true},ship:'brig',daily:{d:"+day+",st:1}})")
  for pg in(A,B):pg.click('#goOpen');pg.wait_for_timeout(400);pg.click('#joingoogle');pg.wait_for_timeout(600);pg.click('#joingo')
  for pg in(A,B):pg.wait_for_function("__t.state==='play'",timeout=90000);pg.evaluate('__t.noAI()')
  EA("P.x=60;P.z=40");EB("P.x=60;P.z=24");A.wait_for_timeout(3000)
  EA("openMenu()");A.wait_for_timeout(200);A.click('#menufriends');A.wait_for_timeout(500)
  A.locator('#friendbody .shipbtn',has_text='Waves').first.click();A.wait_for_timeout(300);print('A:',A.inner_text('#friendmsg'))
  B.wait_for_function("!document.getElementById('coopov').hidden",timeout=20000);B.screenshot(path=D+'co_offer.png');B.click('#coopyes')
  A.wait_for_function("__t.ev('!!coop')",timeout=20000)
  print('islands match:',EA("islands.map(i=>[Math.round(i.x),Math.round(i.z)]).join(';')")==EB("islands.map(i=>[Math.round(i.x),Math.round(i.z)]).join(';')"));print('roles:',EA("[coop.role,MODE]"),EB("[coop.role,MODE]"))
  A.wait_for_function("__t.enemies.length>0",timeout=90000);B.wait_for_timeout(3000)
  print('host enemies',EA("enemies.length"),'| guest sees',EB("enemies.filter(e=>e.proxy).length"),'| guest sees host ship',EB("!!(coop.other&&coop.other.al)"))
  EA("P.x=0;P.z=0;P.inv=999");EB("P.x=6;P.z=0;P.inv=999");B.wait_for_timeout(2000);B.screenshot(path=D+'co_guest.png');A.screenshot(path=D+'co_host.png')
  # the guest sinks wave 1 with its own cannons
  gB=EB("gold")
  for i in range(8):
    if EA("enemies.length")==0:break
    EA("enemies.forEach(e=>{e.cool=99})");tgt=EB("(()=>{const e=enemies.find(q=>q.proxy);return e?[e.x,e.z]:null})()")
    if not tgt:B.wait_for_timeout(500);continue
    EB(f"P.x={tgt[0]}-10;P.z={tgt[1]};P.a=0;P.v=0;P.cool=0;setAim('front')");B.keyboard.down('Space');B.wait_for_timeout(450);B.keyboard.up('Space');B.wait_for_timeout(700)
  EA("enemies.forEach(e=>e.hp=0)");A.wait_for_function("__t.state==='shop'",timeout=60000);B.wait_for_function("__t.state==='shop'",timeout=60000)
  print('after wave 1: host state',EA("state"),'| guest state',EB("state"),'| guest gold',gB,'->',EB("gold"),'| host gold',EA("gold"))
  B.screenshot(path=D+'co_shop_guest.png')
  A.click('#next');A.wait_for_timeout(500);print('host next button:',A.inner_text('#next'))
  B.click('#next');A.wait_for_timeout(3000);print('host wave',EA("wave"),'state',EA("state"),'| guest wave',EB("wave"),'state',EB("state"))
  # guest goes down, comes back next wave
  EB("P.inv=0;P.hp=1;hurtPlayer()");B.wait_for_timeout(1500);print('guest down:',EB("P.down"),'| host sees guest afloat:',EA("coop.other&&coop.other.al"))
  A.wait_for_function("__t.enemies.length>0",timeout=60000);EA("enemies.forEach(e=>e.hp=0)");A.wait_for_function("__t.state==='shop'",timeout=60000);B.wait_for_function("__t.state==='shop'",timeout=60000);print('wave cleared: guest revived',EB("[P.down,P.hp,state]"))
  print('errors',errs);b.close()
