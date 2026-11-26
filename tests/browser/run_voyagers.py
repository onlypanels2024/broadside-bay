# Season 3 (Voyagers): canoes for sale only in the season, bought through the referee, kept afterwards;
# canoe crews throw stones, spears and arrows. Time is moved with window.__wxShift, so it works whatever today's date is.
import json, os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
U = 'http://127.0.0.1:8766/tests/browser/app-test.html'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots'); os.makedirs(OUT, exist_ok=True)
errors = []
def ms(*a): return int(datetime(*a, tzinfo=timezone.utc).timestamp() * 1000)

with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    ctx = b.new_context(viewport={'width': 400, 'height': 800})
    A = ctx.new_page(); A.on('pageerror', lambda e: errors.append(str(e)))
    E = lambda c: A.evaluate(f"__t.ev({json.dumps(c)})")
    sv = lambda: A.evaluate("window.__fakeTree().saves.google_gary")
    A.goto(U + '?who=gary&referee=1'); A.wait_for_timeout(1500); A.evaluate("localStorage.clear()")
    A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:9000,earned:0,sunk:0,xp:9500,ships:{brig:true},ship:'brig',daily:{d:Math.floor(Date.now()/86400000),st:1}})")
    A.click('#goOpen'); A.wait_for_timeout(400); A.click('#joingoogle'); A.wait_for_timeout(600); A.click('#joingo')
    A.wait_for_function("__t.state==='play'", timeout=90000); A.evaluate('__t.noAI()'); A.wait_for_timeout(1500)
    A.evaluate("document.getElementById('dailyov').hidden=true")
    def dock():
        E("P.x=PORTS[0].x+21;P.z=PORTS[0].z;P.v=0;0"); A.wait_for_timeout(1500); A.click('#dock'); A.wait_for_timeout(1200); A.click('#tabYard'); A.wait_for_timeout(400)
    def undock():
        A.click('#next'); A.wait_for_timeout(800)

    # 1. before the season (November 2026): no canoes in the shipyard
    t = ms(2026, 12, 2, 12); E(f"window.__wxShift={t}-Date.now();window.__refShift=window.__wxShift;0")
    dock()
    assert not A.is_visible('#ship-outrigger'), 'no canoes before Season 3'
    undock()

    # 2. in the season (6 January 2027): all three for sale, buy the outrigger through the referee
    t = ms(2027, 1, 6, 12); E(f"window.__wxShift={t}-Date.now();window.__refShift=window.__wxShift;0")
    assert E("seasonAt(krakenNow()).id") == 'voyagers'
    dock()
    for sid in ('outrigger', 'drua', 'doublecanoe'): assert A.is_visible('#ship-' + sid), sid + ' for sale'
    A.screenshot(path=os.path.join(OUT, 'voy_yard.png'))
    A.click('#ship-outrigger'); A.wait_for_timeout(2500)
    s = sv(); print('after buying:', E("shipId"), 'gold', s.get('gold'), 'ships', s.get('ships'))
    assert E("shipId") == 'outrigger' and s['ships'].get('outrigger') is True and s.get('gold') == 9000 - 700, 'outrigger bought for 700'
    assert E("!!pship.userData.canoe"), 'my ship is a canoe'
    undock()

    # 3. at sea: the crew sling stones (no cannonballs, no gun smoke)
    E("P.x=PORTS[0].x+60;P.z=PORTS[0].z+40;P.v=0;up.broadside=1;if(aim!=='side')toggleAim();firing=true;0"); A.wait_for_timeout(1800)
    assert E("balls.some(b=>b.cw==='sling')"), 'sling stones in the air'
    assert not E("balls.some(b=>b.owner==='p'&&!b.cw)"), 'no cannonballs from a canoe'
    A.screenshot(path=os.path.join(OUT, 'voy_outrigger_firing.png'))
    E("firing=false;0")
    # every canoe builds, and each crew throws its own weapon
    for sid, w in (('drua', 'bow'), ('doublecanoe', 'spear')):
        E(f"owned['{sid}']=true;switchShip('{sid}');firing=true;0"); A.wait_for_timeout(1800)
        assert E("!!pship.userData.canoe") and E(f"balls.some(b=>b.cw==='{w}')"), sid + ' throws ' + w
        A.screenshot(path=os.path.join(OUT, f'voy_{sid}_firing.png'))
        E("firing=false;0")
    E("switchShip('outrigger');0")

    # 4. after the season (3 March 2027): no new canoes for sale, but my outrigger is still mine
    t = ms(2027, 3, 3, 12); E(f"window.__wxShift={t}-Date.now();window.__refShift=window.__wxShift;0")
    assert E("seasonAt(krakenNow()).id") == 'kraken'
    E("delete owned.drua;delete owned.doublecanoe;0")
    dock()
    assert A.is_visible('#ship-outrigger') and not A.is_visible('#ship-drua'), 'kept canoe shown, others gone'
    A.screenshot(path=os.path.join(OUT, 'voy_yard_after.png'))
    b.close()
print('errors', errors)
assert not errors
print('VOYAGERS OK')
