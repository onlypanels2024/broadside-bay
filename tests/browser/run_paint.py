import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:pg.evaluate(f"__t.ev({json.dumps(c)})")
  pg.goto(U+'?who=gary&referee=1');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(2500)
  pg.screenshot(path=D+'c_start.png')
  # ---- main menu shipwright, Open sea, brand-new captain
  pg.click('#goDress');pg.wait_for_timeout(1200)
  print('new captain: locked swatches',E("document.querySelectorAll('#swatches .sw.locked').length"),'of',E("document.querySelectorAll('#swatches .sw').length"),
        '| locked emblems',E("document.querySelectorAll('#emgrid .emt.locked').length"),'| ships enabled',E("[...document.querySelectorAll('#shiprow .shipchip')].filter(b=>!b.disabled).length"))
  pg.screenshot(path=D+'c_dress_new.png')
  pg.click('#sw-s5');print('tap locked red sails ->',pg.inner_text('#dressmsg'),'| paint',E("paint.lk"))
  pg.click('#sw-h3');pg.wait_for_timeout(200);pg.screenshot(path=D+'c_dress_scroll.png');pg.click('#em-3');pg.click('#sw-f1');pg.click('#sw-p2');pg.wait_for_timeout(1500)
  print('after picks:',E("paint.lk"),pg.inner_text('#dressmsg'))
  pg.screenshot(path=D+'c_dress_picked.png')
  pg.click('#dressdone');pg.wait_for_timeout(300)
  print('open save paint (guest/local wish):',pg.evaluate("localStorage.getItem('bb-open-wish')"))
  # ---- Wave battle: an Admiral with every ship
  pg.evaluate("localStorage.setItem('bb-waves-v1',JSON.stringify({gold:500,xp:9500,ships:{brig:true,corvette:true,frigate:true,galleon:true,manowar:true},ship:'brig'}))")
  pg.click('#goDress');pg.wait_for_timeout(300);pg.click('#dmWaves');pg.wait_for_timeout(300)
  print('admiral: locked swatches',E("document.querySelectorAll('#swatches .sw.locked').length"),'| ships enabled',E("[...document.querySelectorAll('#shiprow .shipchip')].filter(b=>!b.disabled).length"))
  pg.click('#dship-manowar');pg.click('#sw-h11');pg.click('#sw-t2');pg.click('#sw-s10');pg.click('#sw-c1');pg.click('#em-11');pg.click('#sw-f2');pg.wait_for_timeout(1800)
  print('admiral picks:',E("[shipId,paint.lk]"));pg.screenshot(path=D+'c_dress_admiral.png')
  # ---- draw your own
  pg.click('#em-35');pg.wait_for_timeout(300)
  box=pg.locator('#pad').bounding_box();cs=box['width']/16
  # a simple skull-and-crossed-cutlass style mark: a ring and a cross, left half then mirror
  cells=[(x,3) for x in range(5,8)]+[(4,4),(3,5),(3,6),(3,7),(4,8),(5,9),(6,9),(7,9),(6,6),(7,12),(6,13),(5,14),(7,11),(7,10)]
  for x,y in cells: pg.mouse.click(box['x']+(x+.5)*cs,box['y']+(y+.5)*cs)
  pg.mouse.move(box['x']+2.5*cs,box['y']+12.5*cs);pg.mouse.down();pg.mouse.move(box['x']+7.5*cs,box['y']+12.5*cs,steps=8);pg.mouse.up()
  pg.click('#padflip');pg.wait_for_timeout(200);pg.screenshot(path=D+'c_pad.png')
  pg.click('#paduse');pg.wait_for_timeout(1800)
  print('drawing used:',E("[paint.lk,paint.dw.length,pad.bits.reduce((a,b)=>a+b,0)]"),pg.inner_text('#dressmsg'))
  pg.screenshot(path=D+'c_dress_drawn.png')
  pg.click('#dressdone');pg.wait_for_timeout(300);print('wave note:',pg.inner_text('#wavenote'))
  # ---- survives a restart and is what you sail
  pg.reload();pg.wait_for_timeout(2500)
  pg.click('#goWaves');pg.wait_for_function("__t.state==='play'");print('sailing in waves:',E("[shipId,paint.lk,paint.dw.slice(0,8)]"))
  pg.wait_for_function("__t.enemies.length>0",timeout=90000);pg.wait_for_timeout(1500);pg.screenshot(path=D+'c_waves_play.png')
  E("enemies.forEach(e=>e.hp=0)");pg.wait_for_function("__t.state==='shop'",timeout=60000)
  pg.click('#tabPaint');pg.wait_for_timeout(1200);pg.screenshot(path=D+'c_harbour_paint.png')
  print('harbour sheet: ship picker hidden',not pg.is_visible('#dressships'),'mode switch hidden',not pg.is_visible('#dressmode'))
  pg.click('#sw-s1');pg.click('#em-6');pg.wait_for_timeout(300);pg.click('#dressdone');pg.wait_for_timeout(300)
  print('back in shop:',pg.is_visible('#shopov'),'| saved:',json.loads(pg.evaluate("localStorage.getItem('bb-waves-v1')"))['paint'])
  # ---- hide drawings toggle
  pg.click('#next');pg.wait_for_function("__t.state==='play'");E("openMenu()");pg.wait_for_timeout(200);pg.click('#drawtog')
  print('menu toggle:',pg.inner_text('#drawtog'),pg.evaluate("localStorage.getItem('bb-hidedraw')"));pg.click('#drawtog')
  print('errors',errs);b.close()
