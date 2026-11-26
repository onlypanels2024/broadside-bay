# Season 3: Te Wheke rises in place of the kraken (Gary's Meshy model, arms bent by the game), and the model
# changes nothing else's colour (CLAUDE.md rule: same scene with and without the model).
import json, os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
U = 'http://127.0.0.1:8766/tests/browser/app-test.html'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots'); os.makedirs(OUT, exist_ok=True)
errors = []
def ms(*a): return int(datetime(*a, tzinfo=timezone.utc).timestamp() * 1000)
SLOT = 480000

with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    ctx = b.new_context(viewport={'width': 400, 'height': 800})
    A = ctx.new_page(); A.on('pageerror', lambda e: errors.append(str(e)))
    E = lambda c: A.evaluate(f"__t.ev({json.dumps(c)})")
    A.goto(U + '?who=gary&referee=1'); A.wait_for_timeout(1500); A.evaluate("localStorage.clear()")
    A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:900,earned:0,sunk:0,xp:9500,daily:{d:Math.floor(Date.now()/86400000),st:1}})")
    A.click('#goOpen'); A.wait_for_timeout(400); A.click('#joingoogle'); A.wait_for_timeout(600); A.click('#joingo')
    A.wait_for_function("__t.state==='play'", timeout=90000); A.evaluate('__t.noAI()'); A.wait_for_timeout(1500)
    A.evaluate("document.getElementById('dailyov').hidden=true")
    E("P.inv=1e9;0")

    def rise_at(t):
        t = (t // SLOT) * SLOT + 20000      # 20 s after a slot starts: it is up
        E(f"window.__wxShift={t}-Date.now();0"); A.wait_for_timeout(1200)
        E("P.x=kraken.x+30;P.z=kraken.z;P.v=0;0"); A.wait_for_timeout(2500)

    # 1. Season 3 (January 2027): Te Wheke, not the kraken
    rise_at(ms(2027, 1, 13, 12))
    assert E("kraken.on") is True and E("kraken.wk") is True, 'Te Wheke is up'
    A.wait_for_function("__t.ev('!!kraken.wkm')", timeout=30000)
    assert E("$('bossname').textContent") == 'Te Wheke'
    A.screenshot(path=os.path.join(OUT, 'wheke_hud.png'))
    E("const o=cam.lookAt.bind(cam);cam.lookAt=function(v){if(window.__cv){cam.position.set(...window.__cv[0]);return o(new THREE.Vector3(...window.__cv[1]))}return o(v)};0")
    E("window.__cv=[[kraken.x+26,13,kraken.z+22],[kraken.x,4,kraken.z]];0"); A.wait_for_timeout(1500)
    A.screenshot(path=os.path.join(OUT, 'wheke_close.png'))
    # an attack: the nearest arm rears up and slams down
    E("window.__cv=null;P.x=kraken.x+20;P.z=kraken.z;kraken.atkT=0;0")
    A.wait_for_function("__t.ev('WK.uSlam.value>.3')", timeout=15000)
    E("window.__cv=[[kraken.x+26,13,kraken.z+22],[kraken.x,4,kraken.z]];0")
    A.screenshot(path=os.path.join(OUT, 'wheke_slam.png'))
    E("window.__cv=null;P.x=kraken.x+30;0")

    # 2. the model changes nothing else: freeze the game, draw the same frame with and without it
    E("window.__cv=[[P.x-4,9,P.z+10],[P.x+24,1,P.z]];0"); A.wait_for_timeout(800)   # looking away from Te Wheke (it is behind the camera)
    A.evaluate("window.requestAnimationFrame=()=>0"); A.wait_for_timeout(300)
    E("kraken.wkm.visible=true;R.render(scene,cam);0"); A.screenshot(path=os.path.join(OUT, 'wheke_color_with.png'))
    E("R.render(scene,cam);0"); A.screenshot(path=os.path.join(OUT, 'wheke_color_with2.png'))
    d0 = ImageChops.difference(Image.open(os.path.join(OUT, 'wheke_color_with.png')).convert('RGB'), Image.open(os.path.join(OUT, 'wheke_color_with2.png')).convert('RGB'))
    print('baseline (same frame drawn twice):', d0.getbbox(), d0.getextrema())
    E("kraken.wkm.visible=false;R.render(scene,cam);0"); A.screenshot(path=os.path.join(OUT, 'wheke_color_without.png'))
    d = ImageChops.difference(Image.open(os.path.join(OUT, 'wheke_color_with.png')).convert('RGB'), Image.open(os.path.join(OUT, 'wheke_color_without.png')).convert('RGB'))
    print('colour difference with/without Te Wheke (off screen):', d.getbbox(), d.getextrema())
    assert d.getbbox() is None, 'the model changed the colour of the rest of the scene'
    b.close()

    # 3. a fresh game in Kraken Season (February 2027): the kraken is back
    b = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    A = b.new_context(viewport={'width': 400, 'height': 800}).new_page(); A.on('pageerror', lambda e: errors.append(str(e)))
    E = lambda c: A.evaluate(f"__t.ev({json.dumps(c)})")
    A.goto(U + '?who=gary&referee=1'); A.wait_for_timeout(1500); A.evaluate("localStorage.clear()")
    A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:900,earned:0,sunk:0,xp:9500,daily:{d:Math.floor(Date.now()/86400000),st:1}})")
    A.click('#goOpen'); A.wait_for_timeout(400); A.click('#joingoogle'); A.wait_for_timeout(600); A.click('#joingo')
    A.wait_for_function("__t.state==='play'", timeout=90000); A.evaluate('__t.noAI()'); A.wait_for_timeout(1500)
    A.evaluate("document.getElementById('dailyov').hidden=true"); E("P.inv=1e9;0")
    rise_at(ms(2027, 2, 24, 12))
    assert E("kraken.on") is True and E("kraken.wk") is False and E("$('bossname').textContent") == 'The Kraken', 'kraken again after Season 3'
    b.close()
print('errors', errors)
assert not errors
print('WHEKE OK')
