# Christmas season, Advent calendar, New Year party and Santa's Evil Helper.
# Time is moved with window.__wxShift (the game's sea clock), so the test works whatever today's date is.
import json, os, time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
U = 'http://127.0.0.1:8766/tests/browser/app-test.html'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots')
os.makedirs(OUT, exist_ok=True)
errors = []
def ms(*a): return int(datetime(*a, tzinfo=timezone.utc).timestamp() * 1000)

with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    ctx = b.new_context(viewport={'width': 390, 'height': 760}, has_touch=True, is_mobile=True)
    A = ctx.new_page(); A.on('pageerror', lambda e: errors.append(str(e)))
    E = lambda c: A.evaluate(f"__t.ev({json.dumps(c)})")
    A.goto(U + '?who=gary&referee=1'); A.wait_for_timeout(1500); A.evaluate("localStorage.clear()")
    A.evaluate("window.__fakeAds={noAds:false};window.__fakeDb.ref('saves/google_gary').set({gold:1000,earned:0,sunk:0,xp:900,daily:{d:Math.floor(Date.now()/86400000),st:1}})")
    A.click('#goOpen'); A.wait_for_timeout(400); A.click('#joingoogle'); A.wait_for_timeout(600); A.click('#joingo')
    A.wait_for_function("__t.state==='play'", timeout=90000); A.evaluate('__t.noAI()'); A.wait_for_timeout(1500)

    # 1. today (before the season): nothing Christmassy
    E("XM.chk=0;0"); A.wait_for_timeout(400)
    assert E("XM.on") in (False, None) or E("seasonAt(krakenNow()).id==='xmas'"), 'no Christmas before the season'
    real_on = E("seasonAt(krakenNow()).id")
    print('season now:', real_on)

    # 2. move the clock to 5 December 2026, 20:05 Malta (19:05 UTC): Christmas, Advent door 5, the boss
    t = ms(2026, 12, 5, 19, 5)
    E(f"window.__wxShift={t}-Date.now();XM.chk=0;0"); A.wait_for_timeout(1500)
    assert E("XM.on") is True, 'Christmas season on'
    assert E("M.grass.map===null"), 'snow on the islands'
    assert E("!!XM.snow"), 'snow falling'
    assert E("!!pship.userData.xl"), 'lights on my ship'
    assert E("islands.some(i=>{if(!i.g||!i.port)return false;let f=false;i.g.traverse(o=>{if(o.isPoints)f=true;});return f;})"), 'tree in the harbour'
    assert E("seasonAt(krakenNow()).n") == 'Christmas is Coming'
    A.wait_for_timeout(1500)
    assert E("elf.on") is True, "Santa's Evil Helper is out"
    A.screenshot(path=os.path.join(OUT, 'xmas_play.png'))
    # sail next to it and check the boss bar
    E("P.x=elf.x+14;P.z=elf.z;P.v=0;0"); A.wait_for_timeout(1500)
    assert E("$('boss').hidden") is False and "Santa" in E("$('bossname').textContent"), 'boss bar'
    A.screenshot(path=os.path.join(OUT, 'xmas_boss.png'))
    # sink it: three hits from me, then the last of its health
    for i in range(3): E("elfHurt({x:elf.x,z:elf.z});0")
    g0 = E("gold"); E("elf.hp=0;0"); A.wait_for_timeout(1200)
    assert E("elf.dead") is True and E("gold") > g0, 'sinking it pays'
    A.wait_for_timeout(1500)
    sv = A.evaluate("window.__fakeDb.ref('saves/google_gary').get().then(s=>s.val())")
    print('referee save ks:', sv.get('ks'), 'gold', sv.get('gold'))
    assert sv.get('ks', {}).get('elf') == 1, 'the referee counted the boss'

    # 3. Advent calendar in the daily panel
    E("openDaily&&openDaily('sea');0") if E("typeof openDaily==='function'") else None
    A.wait_for_timeout(800)
    assert A.is_visible('#advbox'), 'Advent calendar shown'
    assert E("$('advbtn').textContent").startswith('Open door 5'), E("$('advbtn').textContent")
    A.screenshot(path=os.path.join(OUT, 'xmas_advent.png'))
    E("window.__refShift=window.__wxShift;0")   # the test referee uses the same moved clock for this request
    g0 = E("gold"); A.click('#advbtn'); A.wait_for_timeout(1500)
    sv = A.evaluate("window.__fakeDb.ref('saves/google_gary').get().then(s=>s.val())")
    print('advent gold', g0, '->', E("gold"), 'save', sv.get('gold'), sv.get('av'))
    assert E("gold") == g0 + 150 or sv.get('gold') == g0 + 150, 'door 5 pays 150'
    assert 'tomorrow' in E("$('advbtn').textContent")
    sv = A.evaluate("window.__fakeDb.ref('saves/google_gary').get().then(s=>s.val())")
    assert sv.get('av') == 16, sv.get('av')
    E("window.__refShift=0;0"); A.click('#dailyclose'); A.wait_for_timeout(400)

    # 4. New Year party: disco ball, beams, fireworks
    t = ms(2026, 12, 31, 21, 0)
    E(f"window.__wxShift={t}-Date.now();XM.chk=0;0"); A.wait_for_timeout(2500)
    assert E("XM.ny") is True and E("!!XM.disco"), 'disco'
    assert E("eventAt(krakenNow()).id") == 'newyear'
    A.screenshot(path=os.path.join(OUT, 'xmas_newyear.png'))

    # 5. after the season everything goes back
    t = ms(2027, 1, 6, 12, 0)
    E(f"window.__wxShift={t}-Date.now();XM.chk=0;0"); A.wait_for_timeout(1500)
    assert E("XM.on") is False and E("M.grass.map!==null") and not E("!!pship.userData.xl") and not E("!!XM.snow") and not E("!!XM.disco"), 'all back to normal'
    assert E("seasonAt(krakenNow()).id") == 'kraken'
    b.close()
print('errors', errors)
assert not errors
