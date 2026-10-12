# Turns the artifact version of the game into the Android app page (www/index.html).
s=open('src-artifact.html').read()
def rep(a,b,count=1):
    global s
    assert s.count(a)==count,('MISSING/DUP',a[:100],s.count(a));s=s.replace(a,b)

# ---- page shell, local fonts and libraries
rep('<title>Broadside Bay</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Barlow+Semi+Condensed:wght@500;600;700&display=swap">\n<style>',
'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="theme-color" content="#071a24">
<title>Broadside Bay</title>
<style>
@font-face{font-family:"Cinzel";font-weight:600;font-display:swap;src:url(fonts/cinzel-latin-600-normal.woff2) format("woff2")}
@font-face{font-family:"Cinzel";font-weight:800;font-display:swap;src:url(fonts/cinzel-latin-800-normal.woff2) format("woff2")}
@font-face{font-family:"Barlow Semi Condensed";font-weight:500;font-display:swap;src:url(fonts/barlow-semi-condensed-latin-500-normal.woff2) format("woff2")}
@font-face{font-family:"Barlow Semi Condensed";font-weight:600;font-display:swap;src:url(fonts/barlow-semi-condensed-latin-600-normal.woff2) format("woff2")}
@font-face{font-family:"Barlow Semi Condensed";font-weight:700;font-display:swap;src:url(fonts/barlow-semi-condensed-latin-700-normal.woff2) format("woff2")}
:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font-size:14px}
img{max-width:100%}''')
rep('</style>\n\n<canvas id="c"','</style>\n</head>\n<body>\n<canvas id="c"')
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>',
'''<script src="vendor/three.min.js"></script>
<script src="vendor/firebase-app-compat.js"></script>
<script src="vendor/firebase-auth-compat.js"></script>
<script src="vendor/firebase-database-compat.js"></script>
<script src="firebase-config.js"></script>
<script src="js/net-firebase.js"></script>''')
s=s.rstrip()+'\n</body>\n</html>\n'

# ---- sign-in overlay + banned notice
rep('<div class="overlay" id="shopov" hidden>',
'''<div class="overlay" id="joinov" hidden>
  <div class="card">
    <div class="eyebrow">Online open sea</div>
    <h2>Join the fleet</h2>
    <div id="joinsigned" hidden>
      <p>Signed in as <b id="joinname">Captain</b>. Your progress is saved online.</p>
      <button class="btn" id="joingo">Set sail</button>
      <div><button class="linkbtn" id="joinout">Sign out</button></div>
    </div>
    <div id="joinchoose">
      <p>Sign in to save your gold and upgrades on any phone.</p>
      <button class="btn" id="joingoogle">Sign in with Google</button>
      <div class="rule"></div>
      <p>Or sail as a guest. Guest progress is not saved.</p>
      <label class="lbl" for="guestname">Captain name</label>
      <input id="guestname" class="namein" maxlength="16" autocomplete="off" placeholder="e.g. Blackbeard">
      <button class="btn ghost" id="joinguest">Sail as guest</button>
    </div>
    <p class="joinerr" id="joinerr" hidden></p>
    <div><button class="linkbtn" id="joinback">Back</button></div>
  </div>
</div>
<div class="overlay" id="shopov" hidden>''')
rep(".linkbtn.warn{color:#ffb4a6}",
""".linkbtn.warn{color:#ffb4a6}
.namein{display:block;width:100%;box-sizing:border-box;margin-top:6px;padding:12px 14px;border-radius:8px;border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--text);font:600 17px var(--body);text-align:center}
.namein:focus{outline:2px solid var(--brass);outline-offset:1px}
.joinerr{color:#ffb4a6;font-size:14px}""")
rep("<li><b>Open sea (online):</b> other captains who have this game open sail the same sea.",
    "<li><b>Open sea (online):</b> sign in with Google to save your progress, or sail as a guest. Other captains sail the same sea.")
rep("      <li>Tap <b>Menu</b> at the top",
    "      <li>A referee checks every hit between captains, so cheating gets you removed from online play.</li>\n      <li>Tap <b>Menu</b> at the top")

# ---- saving: Google = cloud, guest = nothing, no Firebase at all = this phone
rep("function saveOpen(){if(MODE!=='open')return;try{localStorage.setItem(SAVE_KEY,JSON.stringify({gold,earned,up,sunk}))}catch(e){}}",
"""let saveMode='local';
function saveOpen(){if(MODE!=='open')return;const d={gold:gold|0,earned:earned|0,sunk:sunk|0,up:{...up}};
  if(saveMode==='cloud'){if(FB)FB.save(d);}else if(saveMode==='local'){try{localStorage.setItem(SAVE_KEY,JSON.stringify(d))}catch(e){}}}""")
rep("function startOpen(fresh){","function startOpen(fresh,sv){")
rep("  const sv=fresh?null:loadOpen();","  if(sv===undefined)sv=fresh?null:loadOpen();NET.rs=0;")
rep("  pw={speed:0,rapid:0,side:0};placeAtPort(p);updAim();updChips();","  pw={speed:0,rapid:0,side:0};NET.rs=(NET.rs|0)+1;placeAtPort(p);updAim();updChips();")

# ---- start screen + join flow
rep("function refreshStart(){const sv=loadOpen();",
"""function refreshStart(){
  if(FB){$('savenote').hidden=true;$('newVoyage').hidden=true;$('goOpen').textContent='Open sea';
    const u=FB.user();if(u&&u.google){$('savenote').hidden=false;$('savenote').textContent='Signed in as '+u.name;
      FB.loadSave().then(sv=>{if(!sv)return;$('goOpen').textContent='Continue voyage';$('savenote').textContent=`Signed in as ${u.name} · ${sv.gold|0} gold, ${sv.sunk|0} ships sunk`;
        $('newVoyage').hidden=false;$('newVoyage').textContent='Start a new voyage';$('newVoyage').classList.remove('warn');newArm=false;});}
    return;}
  const sv=loadOpen();""")
rep("  try{localStorage.removeItem(SAVE_KEY)}catch(e){}refreshStart();};",
    "  if(FB){FB.save({gold:0,earned:0,sunk:0,up:{hull:0,sails:0,reload:0,triple:0,broadside:0}});setTimeout(refreshStart,300);return;}\n  try{localStorage.removeItem(SAVE_KEY)}catch(e){}refreshStart();};")
rep("""$('goOpen').onclick=()=>{audio();const b=$('goOpen');if(b.disabled)return;b.disabled=true;b.textContent='Charting the sea…';
  setTimeout(()=>{startOpen(false);b.disabled=false;musPlay();$('start').hidden=true;$('hint').hidden=false;state='play';showBanner(PORTS[0].name);},40);};""",
"""function launchOpen(sv){const b=$('goOpen');b.disabled=true;b.textContent='Charting the sea…';
  setTimeout(()=>{startOpen(false,sv);b.disabled=false;b.textContent='Open sea';musPlay();['start','joinov'].forEach(id=>$(id).hidden=true);$('hint').hidden=false;state='play';showBanner(PORTS[0].name);},40);}
function showJoin(){const u=FB.user();$('joinerr').hidden=true;
  $('joinsigned').hidden=!(u&&u.google);$('joinchoose').hidden=!!(u&&u.google);if(u&&u.google)$('joinname').textContent=u.name;
  try{$('guestname').value=localStorage.getItem('bb-guestname')||'';}catch(e){}
  $('start').hidden=true;$('joinov').hidden=false;}
function joinErr(m){$('joinerr').textContent=m;$('joinerr').hidden=false;}
async function sailOnline(){const u=FB.user();saveMode=u.google?'cloud':'none';goOnline();const sv=u.google?await FB.loadSave():null;launchOpen(sv||null);}
$('goOpen').onclick=()=>{audio();if($('goOpen').disabled)return;
  if(!FB){saveMode='local';launchOpen(undefined);return;}
  if(NET.banned){saveMode='local';launchOpen(undefined);showBanner('Offline: playing solo');return;}
  showJoin();};
$('joinback').onclick=()=>{$('joinov').hidden=true;$('start').hidden=false;refreshStart();};
$('joingo').onclick=()=>{audio();sailOnline();};
$('joingoogle').onclick=async()=>{audio();const b=$('joingoogle');b.disabled=true;b.textContent='Signing in…';
  try{await FB.signInGoogle();goOnline();showJoin();}catch(e){joinErr('Google sign-in did not finish. Try again, or sail as a guest.');}
  b.disabled=false;b.textContent='Sign in with Google';};
$('joinguest').onclick=async()=>{audio();const n=FB.cleanName($('guestname').value);
  if(n.length<2){joinErr('Pick a captain name of 2 to 16 letters or numbers.');return;}
  try{localStorage.setItem('bb-guestname',n);}catch(e){}
  const b=$('joinguest');b.disabled=true;b.textContent='Joining…';
  try{closeOnline();await FB.signInGuest(n);await sailOnline();}catch(e){joinErr('Could not reach the online sea. Check your connection and try again.');}
  b.disabled=false;b.textContent='Sail as guest';};
$('joinout').onclick=async()=>{closeOnline();await FB.signOut();refreshStart();showJoin();};""")

# ---- network: Firebase instead of the Claude live room
rep("""(async()=>{
  try{
    if(!window.claude||!window.claude.use)return;
    const room=await window.claude.use('room');if(!room)return;
    NET.room=room;NET.ok=true;
    try{NET.user=await window.claude.use('user');if(NET.user)NET.myId=await NET.user.id();}catch(e){}
    room.onConnection(()=>{},()=>{NET.room=null;NET.ok=false;});
    room.onPeers(()=>{},()=>{NET.room=null;NET.ok=false;});
  }catch(e){NET.room=null;}
})();""",
"""NET.fb=!!FB;NET.rs=0;
function goOnline(){if(!FB||NET.room||NET.banned)return;const u=FB.user();if(!u)return;
  const R=FB.openRoom();NET.room=R;NET.ok=true;NET.myId=R.uid;NET.peers.forEach(dropRemoteShip);NET.peers.clear();NET.last=null;
  R.onConnection(c=>{NET.ok=c;netUiKey='';});
  R.onReward(r=>{NET.kills++;addGold(r.g|0);updHud();saveOpen();showBanner('You sank '+(FB.cleanName(r.n)||'a captain'));chime(true);});
  R.onBanned(()=>{NET.banned=true;closeOnline();saveMode='none';showBanner('Removed from online play by the referee');});}
function closeOnline(){if(!NET.room)return;const R=NET.room;NET.room=null;NET.ok=false;NET.peers.forEach(dropRemoteShip);NET.peers.clear();NET.last=null;netUiKey='';if(R.close)R.close();}
if(FB)FB.ready.then(()=>{const u=FB.user();if(u&&!u.google){FB.signOut();}else if(u)goOnline();refreshStart();});""")
rep("const NET={room:null,","const FB=window.BBFirebase?window.BBFirebase.init(window.BB_FIREBASE_CONFIG):null;\nconst NET={room:null,")
# refreshStart runs before FB/NET are declared further down; move the first call after the network setup
rep("$('overmenu').onclick=()=>{audio();toMenu();};$('shopmenu').onclick=()=>{audio();toMenu();};\nrefreshStart();",
    "$('overmenu').onclick=()=>{audio();toMenu();};$('shopmenu').onclick=()=>{audio();toMenu();};")
rep("if(FB)FB.ready.then(","refreshStart();\nif(FB)FB.ready.then(")
rep("function netShot(x,z,vx,vz){if(!NET.room)return;NET.shots.push({d:[++NET.shotSeq,+x.toFixed(1),+z.toFixed(1),+vx.toFixed(1),+vz.toFixed(1)],t:clock});",
    "function netShot(x,z,vx,vz){if(!NET.room)return;const st=NET.room.serverNow?NET.room.serverNow():Date.now();NET.shots.push({d:[++NET.shotSeq,+x.toFixed(1),+z.toFixed(1),+vx.toFixed(1),+vz.toFixed(1),st],t:clock});")
rep("  const p={m:atSea?'open':'menu',c:NET.color,id:NET.myId||null};","  const p={m:atSea?'open':'menu',c:NET.color};")
rep("x:+P.x.toFixed(1),z:+P.z.toFixed(1),a:+P.a.toFixed(2),","x:+P.x.toFixed(1),z:+P.z.toFixed(1),a:+(((P.a%TAU)+TAU)%TAU).toFixed(2),rs:NET.rs|0,")
rep("v:+P.v.toFixed(1),hp:P.hp,","v:+Math.max(-9,Math.min(33,P.v)).toFixed(1),hp:Math.max(0,Math.min(maxHp(),P.hp)),")
rep("else Object.assign(p,{al:null,","else Object.assign(p,{rs:null,al:null,")
rep("function remoteName(r){const key=r.by||(r.pr&&r.pr.id);",
    "function remoteName(r){if(r.pr&&typeof r.pr.n==='string'){const n=FB?FB.cleanName(r.pr.n):r.pr.n;if(n.length>=2)return n;}const key=r.by||(r.pr&&r.pr.id);")
rep("      if(pr.kb&&pr.kb===NET.myPeer){NET.kills++;","      if(!NET.fb&&pr.kb&&pr.kb===NET.myPeer){NET.kills++;")
rep("""      const [_,x,z,vx,vz]=sh;if(typeof x!=='number'||Math.hypot(x-P.x,z-P.z)>140)continue;
      const m=new THREE.Mesh(BALL,M.ball);m.castShadow=true;scene.add(m);balls.push({m,x,z,vx:+vx||0,vz:+vz||0,life:1.1,max:1.1,owner:'r',from:p.peer,trail:0});""",
"""      let [_,x,z,vx,vz,st]=sh;if(typeof x!!=='number'||Math.hypot(x-P.x,z-P.z)>140)continue;vx=+vx||0;vz=+vz||0;
      // real-time: the ball has already been flying while it travelled to us, so start it where it is now
      const age=(NET.room&&NET.room.serverNow&&typeof st==='number')?Math.max(0,Math.min(.6,(NET.room.serverNow()-st)/1000)):0;
      // if the ball's path while it was on its way already crossed my ship, it has hit me
      if(age>0&&state==='play'&&MODE==='open'){const dx=vx*age,dz=vz*age,L2=dx*dx+dz*dz;let k=L2>0?((P.x-x)*dx+(P.z-z)*dz)/L2:0;k=Math.max(0,Math.min(1,k));
        const cx=x+dx*k,cz=z+dz*k;if(Math.hypot(P.x-cx,P.z-cz)<P.r+.5){spark(x,1.3,z,{color:'#ffd99a',add:true,s:1.8,life:.1});boom(cx,cz,false);
          if(!inSafe(P)){NET.lastHitBy=p.peer;NET.lastHitT=clock;if(NET.room.reportHit)NET.room.reportHit(p.peer,id,P.x,P.z,st+age*k*1000);hurtPlayer();}continue;}}
      const m=new THREE.Mesh(BALL,M.ball);m.castShadow=true;scene.add(m);balls.push({m,x:x+vx*age,z:z+vz*age,vx,vz,life:1.1-age,max:1.1,owner:'r',from:p.peer,sid:id,trail:0});""".replace("!!==","!=="))
rep("if(!inSafe(P)){NET.lastHitBy=b.from;NET.lastHitT=clock;hurtPlayer();}",
    "if(!inSafe(P)){NET.lastHitBy=b.from;NET.lastHitT=clock;if(NET.fb&&NET.room&&NET.room.reportHit)NET.room.reportHit(b.from,b.sid|0,P.x,P.z,NET.room.serverNow());hurtPlayer();}")
rep("  if(MODE==='open'){NET.deaths++;","  if(MODE==='open'){NET.deaths++;if(NET.fb&&NET.room&&NET.room.reportDeath)NET.room.reportDeath();")
rep("$('onlinetxt').textContent=NET.ok?`${NET.online} online · ${NET.sailing} at sea`:'Offline: playing solo';",
    "$('onlinetxt').textContent=NET.ok?`${NET.online} online · ${NET.sailing} at sea`:(NET.banned?'Offline: removed by the referee':'Offline: playing solo');")
open('www/index.html','w').write(s)
print('built www/index.html',len(s))

