import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:pg.evaluate(f"__t.ev({json.dumps(c)})")
  pg.goto(U+'?who=gary');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  # ---- WAVES: earn XP, rank up
  pg.click('#goWaves');pg.wait_for_function("__t.state==='play'");pg.wait_for_function("__t.enemies.length>0",timeout=90000)
  print('waves start:',E("[RANKS[rankOf(xp)].n,xp,shipId,maxHp(),gold]"),'rankrow visible',pg.is_visible('#rankrow'))
  E("enemies.forEach(e=>e.hp=0)");pg.wait_for_function("__t.state==='shop'",timeout=60000)
  print('after wave 1:',E("[RANKS[rankOf(xp)].n,xp,gold]"))
  pg.click('#tabYard');pg.wait_for_timeout(300);pg.screenshot(path='tests/browser/p_yard_start.png')
  print('corvette button:',pg.inner_text('#ship-corvette'))
  E("addXP(300);gold=20000;renderShop()");pg.wait_for_timeout(2600);print('rank after +300xp:',E("RANKS[rankOf(xp)].n"),'| corvette:',pg.inner_text('#ship-corvette'),'| frigate:',pg.inner_text('#ship-frigate'))
  E("addXP(9000);renderShop()");pg.wait_for_timeout(300)
  pg.click('#ship-manowar');pg.wait_for_timeout(300)
  print('bought manowar:',E("[shipId,maxHp(),P.hp,P.r.toFixed(2),gold]"));pg.screenshot(path='tests/browser/p_yard_bought.png')
  pg.click('#tabUp');pg.click('#buy-broadside');print('broadside:',E("up.broadside"))
  pg.click('#next');pg.wait_for_function("__t.enemies.length>0",timeout=60000)
  E("enemies.forEach(e=>{e.cool=999;e.x=P.x+30;e.z=P.z-30});P.cool=0;aim='front'");pg.keyboard.down('Space');pg.wait_for_timeout(120);pg.keyboard.up('Space')
  print('bow volley balls:',E("balls.filter(b=>b.owner==='p').length"))
  E("balls.forEach(b=>{b.life=0});P.cool=0;setAim('side')");pg.keyboard.down('Space');pg.wait_for_timeout(120);pg.keyboard.up('Space')
  print('broadside balls:',E("balls.filter(b=>b.owner==='p'&&b.life>0).length"))
  pg.keyboard.down('Space');pg.wait_for_timeout(1500);pg.keyboard.up('Space');pg.screenshot(path='tests/browser/p_manowar.png')
  E("toMenu()");pg.wait_for_timeout(300);print('wave note:',pg.inner_text('#wavenote'))
  # ---- persistence after reload
  pg.reload();pg.wait_for_timeout(2500);print('after reload wave note:',pg.inner_text('#wavenote'))
  pg.click('#goWaves');pg.wait_for_function("__t.state==='play'");print('waves career kept:',E("[shipId,RANKS[rankOf(xp)].n,gold,up.broadside]"))
  E("toMenu()")
  # ---- open sea is separate
  pg.click('#goOpen');pg.wait_for_timeout(400);pg.fill('#guestname','Gary');pg.click('#joinguest');pg.wait_for_function("__t.state==='play'",timeout=90000)
  print('open sea career (separate):',E("[shipId,RANKS[rankOf(xp)].n,xp,gold]"))
  print('errors',errs);b.close()
