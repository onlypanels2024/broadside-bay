# Season 3 sea monsters: each comes out in its own window (Giant Clam by an island, Reef Serpent circling, Storm Bird in a storm),
# can only be hurt at the right moment, hurts ships, shares its health and pays once beaten (the clam's pearl adds 300).
import json, os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
U = 'http://127.0.0.1:8766/tests/browser/app-test.html'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots'); os.makedirs(OUT, exist_ok=True)
errors = []
def ms(*a): return int(datetime(*a, tzinfo=timezone.utc).timestamp() * 1000)

def game(pw):
    b = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    A = b.new_context(viewport={'width': 400, 'height': 800}).new_page(); A.on('pageerror', lambda e: errors.append(str(e)))
    E = lambda c: A.evaluate(f"__t.ev({json.dumps(c)})")
    A.goto(U + '?who=gary&referee=1'); A.wait_for_timeout(1500); A.evaluate("localStorage.clear()")
    A.evaluate("window.__fakeDb.ref('saves/google_gary').set({gold:0,earned:0,sunk:0,xp:9500,daily:{d:Math.floor(Date.now()/86400000),st:1}})")
    A.click('#goOpen'); A.wait_for_timeout(400); A.click('#joingoogle'); A.wait_for_timeout(600); A.click('#joingo')
    A.wait_for_function("__t.state==='play'", timeout=90000); A.evaluate('__t.noAI()'); A.wait_for_timeout(1500)
    A.evaluate("document.getElementById('dailyov').hidden=true")
    E("const o=cam.lookAt.bind(cam);cam.lookAt=function(v){if(window.__cv){cam.position.set(...window.__cv[0]);return o(new THREE.Vector3(...window.__cv[1]))}return o(v)};0")
    return b, A, E

def window_of(E, kind, pearl=None):
    # the first window of this monster in Season 3 (the same one everyone online sees)
    return E(f"(()=>{{let s=Math.floor({ms(2027,1,5)}/SEAM.slot);for(let k=0;k<9000;k++,s++){{if(seamKind(s)!=='{kind}')continue;{'' if pearl is None else ('if(seamPearl(s)!==' + ('true' if pearl else 'false') + ')continue;')}return s;}}return -1;}})()")

with sync_playwright() as pw:
    # 0. before Season 3 there are none
    b, A, E = game(pw)
    assert E(f"(()=>{{let n=0;for(let s=Math.floor({ms(2026,11,1)}/SEAM.slot),e=s+4000;s<e;s++)if(seamKind(s))n++;return n}})()") == 0
    for kind in ('clam', 'serpent', 'bird'):
        slot = window_of(E, kind, True if kind == 'clam' else None)
        assert slot > 0, kind
        t = slot * 600000 + 30000
        E(f"window.__wxShift={t}-Date.now();window.__refShift=window.__wxShift;P.inv=1e9;0")
        A.wait_for_function("__t.ev('seam.on&&!!seam.g')", timeout=60000)
        assert E("seam.kind") == kind and E("seam.slot") == slot
        E("P.x=seam.cx+30;P.z=seam.cz+6;P.v=0;0"); A.wait_for_timeout(2500)
        assert E("$('bossname').textContent") == E("SEAM.n[seam.kind]"), 'boss bar'
        if kind == 'bird':
            assert E("weatherAt(krakenNow()).rain") > .9, 'the Storm Bird brings a storm'
        A.screenshot(path=os.path.join(OUT, f'seam_{kind}.png'))
        # a shot only counts at the right moment
        E("seam.vuln=false;window.__h0=seam.hp;seamShot({x:seam.x,z:seam.z,life:1});0")
        assert E("seam.hp===window.__h0"), kind + ' cannot be hurt when guarded'
        # it hurts a ship that comes close
        E("P.inv=0;P.hp=P.max||9;window.__p0=P.hp;0")
        if kind == 'clam':
            E("P.x=seam.x+20;P.z=seam.z;P.v=0;seam.shut=false;0"); A.wait_for_function("__t.ev('seam.shut')", timeout=15000)
            assert E("clamJets.length>0"), 'the water jet is in the air'
            A.wait_for_function("__t.ev('P.hp<window.__p0')", timeout=20000)   # the jet lands on the ship
        elif kind == 'serpent':
            E("seam.bit=0;seam.y=0;0"); A.wait_for_timeout(50); E("P.x=seam.x+Math.cos(seam.a)*14;P.z=seam.z+Math.sin(seam.a)*14;P.v=0;0"); A.wait_for_timeout(600)
        else:
            E("P.x=seam.x+12;P.z=seam.z;P.v=0;seam.mode='idle';seam.atkT=0;0"); A.wait_for_function("__t.ev('seam.mode===\"climb\"')", timeout=20000)
            A.screenshot(path=os.path.join(OUT, 'seam_bird_dive.png'))
        A.wait_for_timeout(300)
        print(kind, 'hull before/after its attack:', E("window.__p0"), E("P.hp"))
        assert E("P.hp<window.__p0"), kind + ' hurts ships'
        E("P.inv=1e9;P.hp=P.max||9;0")
        # shared health: the last 4 hits sink it, and the referee pays
        # (the test referee checks the ship's position report against the real clock, and each claim needs 10 minutes since the last)
        E("window.__refShift=0;0"); A.evaluate("window.__fakeDb.ref('saves/google_gary/rl').remove()")
        A.evaluate(f"window.__fakeDb.ref('seam/{slot}').set({{hp:4,hits:{{google_gary:0}}}})"); A.wait_for_timeout(600)
        g0 = A.evaluate("window.__fakeTree().saves.google_gary.gold||0")
        for i in range(4): E("seam.vuln=true;seamShot({x:seam.x,z:seam.z,life:1});0"); A.wait_for_timeout(300)
        A.wait_for_timeout(3500)
        log = [l for l in A.evaluate('window.__refLog') if l[0] == 'req' and l[2] == 'seam']
        g1 = A.evaluate("window.__fakeTree().saves.google_gary.gold||0")
        print(kind, 'dead', E("seam.dead"), 'claim', log[-1:], 'gold', g0, '->', g1)
        assert E("seam.dead") and log and log[-1][3] is True
        assert g1 - g0 == (1800 if kind == 'clam' else 1500), 'paid'
    b.close()
print('errors', errors)
assert not errors
print('SEAM OK')
