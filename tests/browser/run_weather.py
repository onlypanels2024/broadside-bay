import json
from playwright.sync_api import sync_playwright
U='http://127.0.0.1:8766/tests/browser/app-test.html'
D='tests/browser/'
with sync_playwright() as pw:
  b=pw.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']);ctx=b.new_context(viewport={'width':400,'height':800})
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  E=lambda c:pg.evaluate(f"__t.ev({json.dumps(c)})")
  pg.goto(U+'?who=gary&referee=1');pg.wait_for_timeout(2500);pg.evaluate("localStorage.clear()")
  pg.click('#goWaves');pg.wait_for_function("__t.state==='play'");E("__t.noAI&&__t.noAI()");pg.wait_for_timeout(1000)
  # find a moment for each look (searching forward from now, in steps of 30 s)
  want={'day_clear':"w.day>.95&&w.kind==='clear'&&w.cloud<.05",'sunset':"w.dusk>.8&&w.cloud<.05",'night_clear':"w.day<.03&&w.kind==='clear'&&w.cloud<.05",
        'day_storm':"w.day>.95&&w.kind==='storm'&&w.rain>.95",'night_storm':"w.day<.05&&w.kind==='storm'&&w.rain>.95",'day_fog':"w.day>.95&&w.kind==='fog'&&w.fog>.95"}
  for name,cond in want.items():
    sh=E(f"(()=>{{const t0=Date.now();for(let k=0;k<120000;k++){{const w=weatherAt(t0+k*5000);if({cond})return k*5000;}}return -1;}})()")
    if sh<0:print('no moment for',name);continue
    E(f"window.__wxShift={sh};WX.envT=0;WX.thunderT=.3");pg.wait_for_timeout(2600)
    print(name,'shift',round(sh/60000),'min',E("[WX.night.toFixed(2),WX.dusk.toFixed(2),WX.cloud.toFixed(2),WX.fog.toFixed(2),WX.rain.toFixed(2),WAMP.toFixed(2),rain.visible]"))
    pg.screenshot(path=D+f'w_{name}.png')
  E("openMenu()");pg.wait_for_timeout(200);pg.click('#wxtog');print('toggle:',pg.inner_text('#wxtog'),'| rain visible',E("rain.visible"))
  print('errors',errs);b.close()
