# Open sea harbour ad: free for the first docks, then at most one every few minutes, never with No ads.
import json
from playwright.sync_api import sync_playwright
U = 'http://127.0.0.1:8766/tests/browser/app-test.html'
errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    A = b.new_context(viewport={'width': 390, 'height': 760}, has_touch=True, is_mobile=True).new_page()
    A.on('pageerror', lambda e: errors.append(str(e)))
    E = lambda c: A.evaluate(f"__t.ev({json.dumps(c)})")
    A.goto(U + '?who=gary&referee=1'); A.wait_for_timeout(1500); A.evaluate("localStorage.clear()")
    A.evaluate("window.__fakeAds={noAds:false};window.__fakeDb.ref('saves/google_gary').set({gold:100,earned:0,sunk:0,xp:0,daily:{d:Math.floor(Date.now()/86400000),st:1}})")
    A.click('#goOpen'); A.wait_for_timeout(400); A.click('#joingoogle'); A.wait_for_timeout(600); A.click('#joingo')
    A.wait_for_function("__t.state==='play'", timeout=90000); A.evaluate('__t.noAI()'); A.wait_for_timeout(1000)
    def dock():
        E("$('dock').hidden=false;$('dock').click();0"); A.wait_for_timeout(700)
        shop = E("state"); E("$('next').click();0"); A.wait_for_timeout(400)
        return shop
    seen = []
    for i in range(4):
        st = dock(); seen.append((st, E("window.__fakeAds.inter|0")))
        if i == 2: E("AD.last=Date.now()-5*60000;0")   # five minutes later
    print('docks (state, ads shown):', seen)
    assert [x[1] for x in seen] == [0, 0, 1, 2], 'free twice, then an ad, then next one only after the gap'
    assert all(x[0] != 'play' for x in seen), 'the harbour still opens every time'
    E("AD.last=0;window.__fakeAds.noAds=true;0"); n0 = E("window.__fakeAds.inter|0"); dock()
    assert E("window.__fakeAds.inter|0") == n0, 'never with No ads'
    E("window.__fakeAds.noAds=false;AD.last=Date.now();0"); n0 = E("window.__fakeAds.inter|0"); dock()
    assert E("window.__fakeAds.inter|0") == n0, 'not twice within the gap'
    b.close()
print('errors', errors)
assert not errors
