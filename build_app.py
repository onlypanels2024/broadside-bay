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

# ---- saving: Google = cloud, guest = nothing, no Firebase at all = this phone
rep("function saveOpen(){if(MODE!=='open')return;try{localStorage.setItem(SAVE_KEY,JSON.stringify(careerData()))}catch(e){}}",
"""let saveMode='local';
function saveOpen(){if(MODE!=='open')return;const d=careerData();
  if(saveMode==='local'){try{localStorage.setItem(SAVE_KEY,JSON.stringify(d))}catch(e){}}}""")
rep("function startOpen(fresh){","function startOpen(fresh,sv){")
rep("  const sv=fresh?null:loadOpen();","  if(sv===undefined)sv=fresh?null:loadOpen();NET.rs=0;")
rep("  pw={speed:0,rapid:0,side:0};placeAtPort(p);updAim();updChips();","  pw={speed:0,rapid:0,side:0};NET.rs=(NET.rs|0)+1;placeAtPort(p);updAim();updChips();")

# ---- start screen + join flow
rep("function refreshStart(){waveNote();storyNote();tutNote();seasonLine();const sv=loadOpen();",
"""function refreshStart(){waveNote();storyNote();tutNote();seasonLine();
  if(FB){$('savenote').hidden=true;$('newVoyage').hidden=true;$('goOpen').textContent='Open sea';
    const u=FB.user();if(u&&u.google){$('savenote').hidden=false;$('savenote').textContent='Signed in as '+u.name;
      FB.loadSave().then(sv=>{if(!sv)return;$('goOpen').textContent='Continue voyage';$('savenote').textContent=`Signed in as ${u.name} · ${RANKS[rankOf(sv.xp|0)].n} · ${shipById(sv.ship).name} · ${sv.gold|0} gold`;
        $('newVoyage').hidden=false;$('newVoyage').textContent='Start a new voyage';$('newVoyage').classList.remove('warn');newArm=false;});}
    return;}
  const sv=loadOpen();""")
rep("  try{localStorage.removeItem(SAVE_KEY)}catch(e){}refreshStart();};",
    "  if(FB){FB.request({k:'reset'});$('newVoyage').textContent='Starting a new voyage…';setTimeout(refreshStart,2500);return;}\n  try{localStorage.removeItem(SAVE_KEY)}catch(e){}refreshStart();};")
rep("""$('goOpen').onclick=()=>{audio();const b=$('goOpen');if(b.disabled)return;b.disabled=true;b.textContent='Charting the sea…';
  setTimeout(()=>{startOpen(false);b.disabled=false;musPlay();$('start').hidden=true;$('hint').hidden=false;state='play';showBanner(PORTS[0].name);},40);};""",
"""function launchOpen(sv){const b=$('goOpen');b.disabled=true;b.textContent='Charting the sea…';
  setTimeout(()=>{startOpen(false,sv);b.disabled=false;b.textContent='Open sea';musPlay();['start','joinov'].forEach(id=>$(id).hidden=true);$('hint').hidden=false;state='play';showBanner(PORTS[0].name);},40);}
function showJoin(){const u=FB.user();$('joinerr').hidden=true;
  $('joinsigned').hidden=!(u&&u.google);$('joinchoose').hidden=!!(u&&u.google);if(u&&u.google)$('joinname').textContent=u.name;
  try{$('guestname').value=localStorage.getItem('bb-guestname')||'';}catch(e){}
  $('start').hidden=true;$('joinov').hidden=false;}
function joinErr(m){$('joinerr').textContent=m;$('joinerr').hidden=false;}
async function sailOnline(){saveMode='server';goOnline();const sv=await FB.loadSave();launchOpen(sv||null);}
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
  R.onReward(r=>{NET.kills++;showBanner(r.d?'Duel won: +100 gold':'You sank '+(FB.cleanName(r.n)||'a captain'));chime(true);});
  NET.pending=new Map();NET.srv=null;NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;econSync();});
  R.onBanned(()=>{NET.banned=true;closeOnline();saveMode='none';showBanner('Removed from online play by the referee');});}
function closeOnline(){if(NET.unwatch){NET.unwatch();NET.unwatch=null;}if(!NET.room)return;const R=NET.room;NET.room=null;NET.ok=false;NET.peers.forEach(dropRemoteShip);NET.peers.clear();NET.last=null;netUiKey='';if(R.close)R.close();}
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
rep("else Object.assign(p,{sh:null,qc:null,lk:null,dw:null,al:null,","else Object.assign(p,{sh:null,qc:null,lk:null,dw:null,rs:null,al:null,")
rep("function remoteName(r){const key=r.by||(r.pr&&r.pr.id);",
    "function remoteName(r){if(r.pr&&typeof r.pr.n==='string'){const n=FB?FB.cleanName(r.pr.n):r.pr.n;if(n.length>=2)return n;}const key=r.by||(r.pr&&r.pr.id);")
rep("      if(pr.kb&&pr.kb===NET.myPeer){NET.kills++;","      if(!NET.fb&&pr.kb&&pr.kb===NET.myPeer){NET.kills++;")
rep("""      const [_,x,z,vx,vz]=sh;if(typeof x!=='number'||Math.hypot(x-P.x,z-P.z)>140)continue;
      const m=new THREE.Mesh(BALL,ballMat(cosOf(pr.cx).ball));m.castShadow=true;scene.add(m);balls.push({m,x,z,vx:+vx||0,vz:+vz||0,life:1.1,max:1.1,owner:'r',from:p.peer,trail:0});""",
"""      let [_,x,z,vx,vz,st]=sh;if(typeof x!!=='number'||Math.hypot(x-P.x,z-P.z)>140)continue;vx=+vx||0;vz=+vz||0;
      // real-time: the ball has already been flying while it travelled to us, so start it where it is now
      const age=(NET.room&&NET.room.serverNow&&typeof st==='number')?Math.max(0,Math.min(.6,(NET.room.serverNow()-st)/1000)):0;
      // if the ball's path while it was on its way already crossed my ship, it has hit me
      if(age>0&&state==='play'&&MODE==='open'&&!isMate(p.peer)){const dx=vx*age,dz=vz*age,L2=dx*dx+dz*dz;let k=L2>0?((P.x-x)*dx+(P.z-z)*dz)/L2:0;k=Math.max(0,Math.min(1,k));
        const cx=x+dx*k,cz=z+dz*k;if(Math.hypot(P.x-cx,P.z-cz)<P.r+.5){spark(x,1.3,z,{color:'#ffd99a',add:true,s:1.8,life:.1});boom(cx,cz,false);
          if(!inSafe(P)){NET.lastHitBy=p.peer;NET.lastHitT=clock;if(NET.room.reportHit)NET.room.reportHit(p.peer,id,P.x,P.z,st+age*k*1000);hurtPlayer();}continue;}}
      const m=new THREE.Mesh(BALL,ballMat(cosOf(pr.cx).ball));m.castShadow=true;scene.add(m);balls.push({m,x:x+vx*age,z:z+vz*age,vx,vz,life:1.1-age,max:1.1,owner:'r',from:p.peer,sid:id,trail:0});""".replace("!!==","!=="))
rep("if(!inSafe(P)){NET.lastHitBy=b.from;NET.lastHitT=clock;hurtPlayer();}",
    "if(!inSafe(P)){NET.lastHitBy=b.from;NET.lastHitT=clock;if(NET.fb&&NET.room&&NET.room.reportHit)NET.room.reportHit(b.from,b.sid|0,P.x,P.z,NET.room.serverNow());hurtPlayer();}")
rep("  if(MODE==='open'){NET.deaths++;","  if(MODE==='open'){NET.deaths++;if(NET.fb&&NET.room&&NET.room.reportDeath)NET.room.reportDeath();")
rep("$('onlinetxt').textContent=NET.ok?`${NET.online} online · ${NET.sailing} at sea`:'Offline: playing solo';",
    "$('onlinetxt').textContent=NET.ok?`${NET.online} online · ${NET.sailing} at sea`:(NET.banned?'Offline: removed by the referee':'Offline: playing solo');")
# ---- economy: the online referee alone decides gold, XP, upgrades and ships in online Open sea
rep("function econServer(){return false;}\nfunction econRequest(r){}\nfunction econKill(kind,id){",
"""function econServer(){return MODE==='open'&&saveMode==='server'&&!!NET.room;}
function econRequest(r){if(!econServer())return;const k=FB.request(r);if(k)NET.pending.set(k,Date.now());}
// Online kill rewards include the coins the wreck drops (coins online are just for show).
const ONLINE_KILL={sloop:{g:70,xp:20},galleon:{g:210,xp:50},fireship:{g:120,xp:35},boss:{g:550,xp:250},treasure:{g:400,xp:60},merchant:{g:500,xp:80},escort:{g:300,xp:70},kraken:{g:900,xp:400}};
// Show the reward straight away, then follow the referee's answer: while requests are waiting we keep
// the local numbers; once all are answered we take the referee's numbers (correcting anything refused).
function econSync(){const sv=NET.srv;if(!sv||!econServer())return;const last=typeof sv.last==='string'?sv.last:'';
  for(const [k,t] of NET.pending)if(k<=last||Date.now()-t>20000)NET.pending.delete(k);
  if(NET.pending.size)return;
  gold=sv.gold|0;earned=sv.earned|0;sunk=sv.sunk|0;up=Object.assign({hull:0,sails:0,reload:0,triple:0,broadside:0},sv.up||{});
  xp=sv.xp|0;owned=Object.assign({brig:true},sv.ships||{});const want=owned[sv.ship]?sv.ship:'brig';if(want!==shipId)setShip(want);
  if(P.hp>maxHp())P.hp=maxHp();updHud();updXP();updAim();if(state==='shop')renderShop();}
function econKill(kind,id){if(econServer()){const K=ONLINE_KILL[kind]||ONLINE_KILL.sloop;addGold(Math.round(K.g*eventMul(kind,serverNowMs())));addXP(K.xp);if(IS_SHIP(kind))sunk++;econRequest(id!==undefined?{k:'kill',e:kind,id:String(id)}:{k:'kill',e:kind});return;}
  """)
rep("  uniT-=dt;if(uniT<=0){uniT=.5;streamIslands();setIslandUniforms();updQuestChip();}","  uniT-=dt;if(uniT<=0){uniT=.5;streamIslands();setIslandUniforms();updQuestChip();if(NET.pending&&NET.pending.size)econSync();}")
# ---- ship paint online: other captains only ever see colours the referee has approved
rep("sh:SHIPS.indexOf(SHIP()),qc:myChat,lk:paint.lk,dw:paint.dw||null,",
    "sh:SHIPS.indexOf(SHIP()),qc:myChat,lk:netPaint().lk||null,dw:netPaint().dw||null,")
rep("function econServer(){return MODE==='open'&&saveMode==='server'&&!!NET.room;}",
"""function econServer(){return MODE==='open'&&saveMode==='server'&&!!NET.room;}
// What we tell other captains: online, only the referee's copy (the database refuses anything else).
function netPaint(){if(!(NET.fb&&saveMode==='server'))return paint;const sp=NET.srv&&NET.srv.paint;return sp&&typeof sp.lk==='string'?sp:{};}""")
rep("  xp=sv.xp|0;owned=Object.assign({brig:true},sv.ships||{});const want=owned[sv.ship]?sv.ship:'brig';if(want!==shipId)setShip(want);",
    "  xp=sv.xp|0;owned=Object.assign({brig:true},sv.ships||{});const want=owned[sv.ship]?sv.ship:'brig';\n  const np=cleanPaint(sv.paint,xp),pc=!showcase&&(np.lk!==paint.lk||np.dw!==paint.dw);\n  if(pc&&paint.dw&&!np.dw&&!(sv.dok&&sv.dok[paint.dw])){okDrawings=okDrawings.filter(d=>d!==paint.dw);try{localStorage.setItem('bb-dok',JSON.stringify(okDrawings))}catch(e){}showBanner('Your drawing was removed after a report');}\n  if(pc)paint=np;if(want!==shipId||pc)setShip(want);")
# main-menu shipwright for online Open sea: show the last copy of the online save; remember the choice and
# hand it to the referee when the captain sets sail
rep("function dressLoad(m){return m==='waves'?loadWaves():loadOpen();}",
"""const WISH_KEY='bb-open-wish',CACHE_KEY='bb-srv-cache';
function srvCache(){if(!FB)return null;const u=FB.user();try{const c=JSON.parse(localStorage.getItem(CACHE_KEY)||'null');return u&&u.google&&c&&c.uid===u.uid?c.sv:null;}catch(e){return null;}}
function cacheSave(sv){const u=FB&&FB.user();if(!u||!u.google||!sv)return;try{localStorage.setItem(CACHE_KEY,JSON.stringify({uid:u.uid,sv:{xp:sv.xp|0,ships:sv.ships||{brig:true},ship:sv.ship,paint:sv.paint||null}}))}catch(e){}}
function openWish(){try{return JSON.parse(localStorage.getItem(WISH_KEY)||'null')}catch(e){return null}}
function dressLoad(m){if(m==='waves')return loadWaves();if(!FB)return loadOpen();
  const base=srvCache()||{xp:0,ships:{brig:true},ship:'brig'},w=openWish();if(!w)return base;return Object.assign({},base,w.ship?{ship:w.ship}:{},w.paint?{paint:w.paint}:{});}
function applyWish(){const w=openWish();try{localStorage.removeItem(WISH_KEY)}catch(e){}if(!w)return;
  if(w.ship&&owned[w.ship]&&w.ship!==shipId){setShip(w.ship);econRequest({k:'ship',id:w.ship});}
  if(w.paint&&paintOk(w.paint,xp)){const np=cleanPaint(w.paint,xp);if(np.lk!==paint.lk||np.dw!==paint.dw){paint=np;setShip(shipId);econRequest({k:'look',lk:np.lk,dw:np.dw||''});}}
  updHud();}""")
rep("  else{const v=loadOpen()||{gold:0,earned:0,sunk:0,",
    "  else if(FB){try{localStorage.setItem(WISH_KEY,JSON.stringify({ship:shipId,paint:{...paint}}))}catch(e){}}\n  else{const v=loadOpen()||{gold:0,earned:0,sunk:0,")
rep("  setTimeout(()=>{startOpen(false,sv);b.disabled=false;",
    "  setTimeout(()=>{startOpen(false,sv);if(FB&&saveMode==='server')applyWish();b.disabled=false;")
rep("NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;econSync();});",
    "NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;cacheSave(sv);econSync();});")
rep("      FB.loadSave().then(sv=>{if(!sv)return;",
    "      FB.loadSave().then(sv=>{if(!sv)return;cacheSave(sv);")
# ---- drawings: the online referee checks every new drawing (built-in rules + AI) before it can be used
rep("function drawCheck(dw){return Promise.resolve({ok:true});}",
"""function drawCheck(dw){if(!FB)return Promise.resolve({ok:true});
  return new Promise(async res=>{let off=null,timer=null;const fin=v=>{if(off)off();clearTimeout(timer);res(v);};
    try{await FB.ensureUser();}catch(e){fin({ok:false,why:'checker offline'});return;}
    const key=FB.request({k:'check',dw});if(!key){fin({ok:false,why:'checker offline'});return;}
    timer=setTimeout(()=>fin({ok:false,why:'checker offline'}),45000);
    off=FB.watchSave(sv=>{if(!sv||typeof sv.last!=='string'||sv.last<key)return;
      if(sv.dok&&sv.dok[dw])fin({ok:true});else if(sv.dchk&&sv.dchk.dw===dw)fin({ok:false,why:sv.dchk.why});else fin({ok:false,why:'checker offline'});});});}
// when the checker is down, show its last error in small print (helps fix it)
const _dc=drawCheck;drawCheck=async dw=>{const v=await _dc(dw);if(!v.ok&&v.why==='checker offline'&&FB){const st=await FB.checkerStatus();
  if(st&&!st.ok&&st.err)setTimeout(()=>{$('padmsg').textContent+=' (Details: '+String(st.err).slice(0,120)+')';},0);}return v;};""")
rep("function reportDrawing(tg,dw){}","function reportDrawing(tg,dw){if(FB)FB.report(tg,dw);}")
# ---- daily chest and quests: online Open sea, paid by the referee
rep("function dailyOn(){return false;}","function dailyOn(){return econServer()&&!!NET.srv;}")
rep("function dailySave(){return null;}","function dailySave(){return NET.srv;}")
rep("  setTimeout(()=>{startOpen(false,sv);if(FB&&saveMode==='server')applyWish();b.disabled=false;",
    "  [2500,6000].forEach(ms=>setTimeout(()=>{if(!daily.auto&&state==='play'&&dailyOn()&&dailyState().canChest&&$('menuov').hidden){daily.auto=true;openDaily('sea');}},ms));\n  setTimeout(()=>{startOpen(false,sv);if(FB&&saveMode==='server')applyWish();b.disabled=false;")
rep("function serverNowMs(){return Date.now();}","function serverNowMs(){return NET.room&&NET.room.serverNow?NET.room.serverNow():Date.now();}")
rep("NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;cacheSave(sv);econSync();});",
    "NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;cacheSave(sv);econSync();dailyNotice();});")
# ---- leaderboards
rep("function boardOn(){return false;}","function boardOn(){return !!FB;}")
rep("function boardLoad(path,field){return Promise.resolve(null);}","async function boardLoad(path,field){try{await FB.ensureUser();}catch(e){return null;}return FB.board(path,field,25);}")
rep("function boardMine(path){return Promise.resolve(null);}","function boardMine(path){return FB.boardMine(path);}")
rep("function myUid(){return null;}","function myUid(){const u=FB&&FB.user();return u?u.uid:null;}")
rep("  if(FB){$('savenote').hidden=true;","  if(FB){$('goBoard').hidden=false;$('savenote').hidden=true;")
# ---- fleets
rep("function fleetOn(){return false;}","function fleetOn(){return econServer()&&!!NET.srv;}")
rep("function fleetGoogle(){return true;}","function fleetGoogle(){const u=FB&&FB.user();return !!(u&&u.google);}")
rep("function fleetsAll(){return {};}","function fleetsAll(){return NET.fleets||{};}")
rep("function myFleetId(){return null;}","function myFleetId(){return (NET.srv&&NET.srv.fleet)||null;}")
rep("function fleetMsg(){return null;}","function fleetMsg(){return NET.srv&&NET.srv.fmsg||null;}")
rep("sh:SHIPS.indexOf(SHIP()),qc:myChat,lk:netPaint().lk||null,","sh:SHIPS.indexOf(SHIP()),fl:myFleetTag()||null,qc:myChat,lk:netPaint().lk||null,")
rep("else Object.assign(p,{sh:null,qc:null,lk:null,dw:null,rs:null,","else Object.assign(p,{sh:null,fl:null,qc:null,lk:null,dw:null,rs:null,")
rep("NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;cacheSave(sv);econSync();dailyNotice();});",
    "NET.unwatch=FB.watchSave(sv=>{NET.srv=sv;cacheSave(sv);econSync();dailyNotice();fleetChanged();});\n  NET.fleets={};NET.unfleets=FB.watchFleets(f=>{NET.fleets=f;fleetChanged();});")
rep("function closeOnline(){if(NET.unwatch){NET.unwatch();NET.unwatch=null;}",
    """// my fleet or any fleet's details changed: redraw my flag, other ships' tags, and the fleet screen
let fleetKey='';
function fleetChanged(){const f=fleetsAll()[myFleetId()],k=f?f.tag+f.col+f.em:'';if(k!==fleetKey){const had=fleetKey;fleetKey=k;if(state!=='title')setShip(shipId);if(had!==''||k!=='')NET.last=null;
    if(k&&!had&&state==='play')showBanner('You sail with ['+f.tag+'] '+f.n);}
  NET.last=null;renderFleet();}
function closeOnline(){if(NET.unwatch){NET.unwatch();NET.unwatch=null;}if(NET.unfleets){NET.unfleets();NET.unfleets=null;}NET.fleets={};fleetKey='';""")
# ---- the shared kraken
rep("function krakenWatch(slot,cb){return ()=>{};}","function krakenWatch(slot,cb){return FB&&NET.room?FB.krakenWatch(slot,cb):()=>{};}")
rep("function krakenHitShared(slot){}","function krakenHitShared(slot){if(FB&&NET.room)FB.krakenHit(slot,kraken.max>60);}")
# ---- captain's log, titles and looks
rep("function logOn(){return false;}","function logOn(){return econServer()&&!!NET.srv;}")
rep("function logSave(){return null;}","function logSave(){return NET.srv;}")
rep("sh:SHIPS.indexOf(SHIP()),fl:myFleetTag()||null,","sh:SHIPS.indexOf(SHIP()),fl:myFleetTag()||null,ti:(NET.srv&&NET.srv.title)||null,cx:(NET.srv&&NET.srv.cx)||null,")
rep("else Object.assign(p,{sh:null,fl:null,","else Object.assign(p,{sh:null,fl:null,ti:null,cx:null,")
rep("econSync();dailyNotice();fleetChanged();});","econSync();dailyNotice();fleetChanged();achNotice();});")
# ---- friends
rep("function friendsOn(){return false;}","function friendsOn(){return econServer()&&!!NET.srv;}")
rep("function friendsData(){return{list:{},reqs:{}};}","function friendsData(){return NET.friends||{list:{},reqs:{}};}")
rep("function friendAsk(uid,name){} function friendAccept(uid,name){} function friendRemove(uid){}",
    "function friendAsk(uid,name){if(fleetGoogle())FB.friendAsk(uid,FB.user().name);else $('friendmsg').textContent='Sign in with Google to add friends.';}\nfunction friendAccept(uid,name){FB.friendAccept(uid,name,FB.user().name);}\nfunction friendRemove(uid){FB.friendRemove(uid);}")
rep("function onlineSet(){return typeof NET!=='undefined'&&NET.onlineIds?NET.onlineIds:new Set();}","function onlineSet(){return NET.room&&NET.room.onlineIds?NET.room.onlineIds():new Set();}")
rep("  NET.fleets={};NET.unfleets=FB.watchFleets(f=>{NET.fleets=f;fleetChanged();});",
    "  NET.fleets={};NET.unfleets=FB.watchFleets(f=>{NET.fleets=f;fleetChanged();});\n  let reqN=-1;NET.friends={list:{},reqs:{}};NET.unfriends=FB.watchFriends(fd=>{NET.friends={list:fd.list,reqs:fd.reqs};const n=Object.keys(fd.reqs).length;if(reqN>=0&&n>reqN&&state==='play')showBanner('New friend request (Menu → Friends)');reqN=n;renderFriends();});")
rep("if(NET.unfleets){NET.unfleets();NET.unfleets=null;}","if(NET.unfleets){NET.unfleets();NET.unfleets=null;}if(NET.unfriends){NET.unfriends();NET.unfriends=null;}NET.friends=null;")
# ---- port battles
rep("function portData(){return null;}","""function portData(){return econServer()?NET.ports||null:null;}
async function loadPorts(){if(!NET.room)return;const wk=weekOf(serverNowMs()),out={hold:[null,null,null],race:[[],[],[]]};
  await Promise.all(PORTS.map(async(p,i)=>{const a=await FB.board('board/p'+(wk-1)+'/'+i,'s',1),b=await FB.board('board/p'+wk+'/'+i,'s',3);if(a&&a[0])out.hold[i]=a[0].uid;if(b)out.race[i]=b;}));
  NET.ports=out;renderFleet();}
setInterval(()=>{if(NET.room&&MODE==='open'&&state!=='title')loadPorts();},30000);""")
rep("  NET.fleets={};NET.unfleets=FB.watchFleets(f=>{NET.fleets=f;fleetChanged();});","  NET.fleets={};NET.unfleets=FB.watchFleets(f=>{NET.fleets=f;fleetChanged();});setTimeout(loadPorts,1500);")
# ---- duels
rep("function duelOn(){return false;}","function duelOn(){return econServer()&&!!NET.srv;}")
rep("function duelSend(uid,ok){}","function duelSend(uid,ok){FB.duelSend(uid,FB.user().name,ok);}")
rep("function duelClear(uid){}","function duelClear(uid){FB.duelClear(uid);}")
rep("sh:SHIPS.indexOf(SHIP()),fl:myFleetTag()||null,","sh:SHIPS.indexOf(SHIP()),du:duel?duel.opp:null,fl:myFleetTag()||null,")
rep("else Object.assign(p,{sh:null,fl:null,","else Object.assign(p,{sh:null,du:null,fl:null,")
rep("  let reqN=-1;NET.friends=","  NET.unduel=FB.duelWatch(duelInbox);\n  let reqN=-1;NET.friends=")
rep("if(NET.unfriends){NET.unfriends();NET.unfriends=null;}","if(NET.unfriends){NET.unfriends();NET.unfriends=null;}if(NET.unduel){NET.unduel();NET.unduel=null;}")
# ---- co-op Wave battle
rep("function coopOn(){return false;}","function coopOn(){return !!(FB&&NET.room);}")
rep("function coopNet(){return null;}","function coopNet(){if(!FB||!NET.room)return null;return{me:NET.myId,invite:(uid,ok)=>FB.coopInvite(uid,FB.user().name,ok),clear:uid=>FB.coopClear(uid),set:(p,v)=>FB.coopSet(p,v),watch:(p,cb)=>FB.coopWatch(p,cb)};}")
rep("  NET.unduel=FB.duelWatch(duelInbox);","  NET.unduel=FB.duelWatch(duelInbox);NET.uncoop=FB.coopInboxWatch(coopInbox);")
rep("if(NET.unduel){NET.unduel();NET.unduel=null;}","if(NET.unduel){NET.unduel();NET.unduel=null;}if(NET.uncoop){NET.uncoop();NET.uncoop=null;}")
# ---- the open sea grows with the number of captains online (size kept on the server, a few bytes)
rep("function worldTierWanted(){return 0;}","""function worldTierWanted(){const w=NET.world,today=Math.floor(serverNowMs()/86400000);return w&&w.day===today?w.tier|0:0;}
const tierFor=n=>n>=40?4:n>=28?3:n>=16?2:n>=8?1:0;
function worldCheck(){if(!FB||!NET.room)return;const today=Math.floor(serverNowMs()/86400000),t=tierFor(NET.online|0);if(t>worldTierWanted()||(t>0&&(!NET.world||NET.world.day!==today)))FB.raiseWorld(today,t);}""")
rep("  NET.online=online;NET.sailing=sailing;","  NET.online=online;NET.sailing=sailing;if(typeof worldCheck==='function')worldCheck();")
rep("  NET.fleets={};NET.unfleets=","  NET.unworld=FB.watchWorld(w=>{NET.world=w;setWorldTier(worldTierWanted());});\n  NET.fleets={};NET.unfleets=")
rep("if(NET.unfleets){NET.unfleets();NET.unfleets=null;}","if(NET.unfleets){NET.unfleets();NET.unfleets=null;}if(NET.unworld){NET.unworld();NET.unworld=null;}")
# ---- starter reward for the first online voyage (the referee gives it once per Google account)
rep("  [2500,6000].forEach(ms=>setTimeout(()=>{","  setTimeout(()=>{try{if(localStorage.getItem('bb-starter')==='1'&&FB.user()&&FB.user().google&&econServer()){econRequest({k:'starter'});addGold(300);updHud();showBanner('Starter reward: 300 gold');localStorage.removeItem('bb-starter');}}catch(e){}},3500);\n  [2500,6000].forEach(ms=>setTimeout(()=>{")
# ---- season rewards
rep("function seasonClaimUI(box){}   // the app: offer last season's reward to its top 10","""function seasonClaimUI(box){const S=seasonAt(serverNowMs()),prev=S.no-1,sv=NET.srv;if(prev<1||!sv||(sv.sr||[]).includes(prev)||!FB)return;
  FB.board('board/s'+prev,'s',10).then(rows=>{if(!rows)return;const me=myUid(),i=rows.findIndex(r=>r.uid===me);if(i<0)return;
    const b=document.createElement('button');b.className='btn small';b.style.display='block';b.style.margin='8px auto 0';b.textContent='Claim: #'+(i+1)+' in season '+prev+' · 1,000 gold';
    b.onclick=()=>{econRequest({k:'season',id:String(prev)});addGold(1000);updHud();b.disabled=true;b.textContent='Claimed ✓';chime(true);showBanner('Season Champion!');};box.appendChild(b);});}""")
# ---- notifications: tokens are saved for the signed-in captain
rep("function notifSaveToken(t){}","function notifSaveToken(t){NET.pushToken=t;if(FB&&FB.user())FB.saveToken(t);}")
rep("function notifSaveTokenClear(){}","function notifSaveTokenClear(){if(FB&&FB.user())FB.clearToken();}")
rep("NET.unwatch=FB.watchSave(sv=>{","if(notifOn&&NET.pushToken)FB.saveToken(NET.pushToken);NET.unwatch=FB.watchSave(sv=>{")
# ---- delete my online data (Google Play requires a way to do this inside the app)
rep("function eraseOn(){return false;}","function eraseOn(){const u=FB&&FB.user();return !!(u&&u.google&&NET.room);}")
rep("function eraseNow(){}","function eraseNow(){FB.request({k:'erase'});try{['bb-srv-cache','bb-open-wish'].forEach(k=>localStorage.removeItem(k));}catch(e){}setTimeout(async()=>{closeMenu();toMenu();closeOnline();await FB.signOut();refreshStart();showBanner('Your online captain has been deleted');},2500);}")
# ---- ads (Google AdMob) and the No ads subscription (Google Play, checked by the referee)
rep("""function adsOn(){return !!window.__fakeAds;}
function noAdsOn(){return !!(window.__fakeAds&&window.__fakeAds.noAds);}
function adReward(){const f=window.__fakeAds;if(f)f.rewarded=(f.rewarded|0)+1;return Promise.resolve(!!f);}
function adInter(){const f=window.__fakeAds;if(f)f.inter=(f.inter|0)+1;return Promise.resolve();}
function noAdsBuy(say){say('Remove ads is only in the Android app.');}
function noAdsPrice(){return '€5';}""","""// Google's test ads until the game goes public (tapping your own real ads breaks AdMob's rules). Set to false for the public release.
const AD_TEST=true;
const AD_IDS={reward:'ca-app-pub-7319579555027884/2523081279',inter:'ca-app-pub-7319579555027884/9177698541'};
const NOADS={sku:'noads_monthly',plan:'monthly'};
const ADST={on:false,rw:false,inr:false,na:0,price:'',synced:0};
try{ADST.na=+localStorage.getItem('bb-noads')||0;}catch(e){}
const capPlug=n=>{const c=window.Capacitor;return c&&c.isNativePlatform&&c.isNativePlatform()&&c.Plugins&&c.Plugins[n]||null;};
function adsOn(){return !!window.__fakeAds||ADST.on;}
function noAdsOn(){return window.__fakeAds?!!window.__fakeAds.noAds:ADST.na>Date.now();}
function adPrep(kind){const A=capPlug('AdMob');if(!A)return;
  const p=kind==='rw'?A.prepareRewardVideoAd({adId:AD_IDS.reward,isTesting:AD_TEST}):A.prepareInterstitial({adId:AD_IDS.inter,isTesting:AD_TEST});
  p.then(()=>{ADST[kind]=true;},()=>{ADST[kind]=false;setTimeout(()=>adPrep(kind),90000);});}
async function adsInit(){const A=capPlug('AdMob');if(!A)return;
  try{await A.initialize({maxAdContentRating:'Teen',initializeForTesting:AD_TEST});}catch(e){return;}
  try{const ci=await A.requestConsentInfo();if(ci&&ci.isConsentFormAvailable&&ci.status==='REQUIRED')await A.showConsentForm();}catch(e){}
  ADST.on=true;adPrep('rw');adPrep('inr');renderNoAds();
  const NP=capPlug('NativePurchases');if(NP)NP.getProduct({productIdentifier:NOADS.sku,productType:'subs'}).then(r=>{if(r&&r.product&&r.product.priceString){ADST.price=r.product.priceString;renderNoAds();}}).catch(()=>{});}
// shows an ad and waits until it is closed; game sound pauses meanwhile
function adShow(kind){const A=capPlug('AdMob');if(!A||!ADST[kind]){adPrep(kind);return Promise.resolve(false);}
  ADST[kind]=false;try{if(ac)ac.suspend();}catch(e){}
  return new Promise(res=>{let got=false,fin=false;const hs=[];
    const done=()=>{if(fin)return;fin=true;hs.forEach(h=>Promise.resolve(h).then(x=>x&&x.remove()).catch(()=>{}));try{if(ac)ac.resume();}catch(e){}adPrep(kind);res(got);};
    if(kind==='rw'){hs.push(A.addListener('onRewardedVideoAdReward',()=>{got=true;}));hs.push(A.addListener('onRewardedVideoAdDismissed',done));hs.push(A.addListener('onRewardedVideoAdFailedToShow',done));
      A.showRewardVideoAd().then(r=>{if(r)got=true;}).catch(done);}
    else{hs.push(A.addListener('interstitialAdDismissed',done));hs.push(A.addListener('interstitialAdFailedToShow',done));A.showInterstitial().catch(done);}
    setTimeout(done,180000);});}
function adReward(){if(window.__fakeAds){window.__fakeAds.rewarded=(window.__fakeAds.rewarded|0)+1;return Promise.resolve(true);}
  if(!ADST.rw){adPrep('rw');showBanner('No video ready yet. Try again in a minute.');return Promise.resolve(false);}
  return adShow('rw').then(ok=>{if(!ok)showBanner('Watch the video to the end for the reward.');return ok;});}
function adInter(){if(window.__fakeAds){window.__fakeAds.inter=(window.__fakeAds.inter|0)+1;return Promise.resolve();}return adShow('inr').then(()=>{});}
function noAdsPrice(){return ADST.price||'€5';}
function noAdsSet(na){ADST.na=na|0;try{localStorage.setItem('bb-noads',ADST.na)}catch(e){}renderNoAds();}
// the referee keeps the paid-until time in this captain's save; when it runs out it asks Google Play again (renewals)
async function noAdsSync(){const u=FB&&FB.user();if(!u||!u.google)return;let sv=null;try{sv=await FB.loadSave();}catch(e){}
  const na=sv&&+sv.na||0;noAdsSet(na);
  if(sv&&sv.na&&na<Date.now()&&Date.now()-ADST.synced>6*3600000){ADST.synced=Date.now();FB.request({k:'noads'});setTimeout(async()=>{try{const s2=await FB.loadSave();noAdsSet(s2&&+s2.na||0);}catch(e){}},15000);}}
async function noAdsBuy(say){if(noAdsOn()){say('No ads is on. Thank you for supporting Broadside Bay! You can cancel any time in Google Play → Payments & subscriptions.');return;}
  const NP=capPlug('NativePurchases'),u=FB&&FB.user();
  if(!NP){say('Remove ads is only in the Android app.');return;}
  if(!u||!u.google){say('Sign in with Google first (Open sea), so No ads follows you to any phone.');return;}
  say('Opening Google Play…');
  try{const t=await NP.purchaseProduct({productIdentifier:NOADS.sku,planIdentifier:NOADS.plan,productType:'subs'});
    const tok=t&&(t.purchaseToken||t.transactionId);if(!tok){say('');return;}
    FB.request({k:'noads',tok});noAdsSet(Date.now()+3600000);say('Thank you! Ads are off. Google Play confirms it in a moment.');
    setTimeout(async()=>{try{const sv=await FB.loadSave();if(sv&&+sv.na)noAdsSet(+sv.na);}catch(e){}},15000);
  }catch(e){const m=String(e&&e.message||e);say(/cancel/i.test(m)?'':'Google Play said: '+m.slice(0,120));}}""")
rep("econSync();dailyNotice();fleetChanged();achNotice();});","econSync();dailyNotice();fleetChanged();achNotice();if(sv&&(+sv.na||0)!==ADST.na&&!(ADST.na>Date.now()&&!sv.na&&ADST.na-Date.now()<3600000))noAdsSet(+sv.na||0);});")
rep("if(FB)FB.ready.then(","adsInit();\nif(FB)FB.ready.then(()=>noAdsSync());\nif(FB)FB.ready.then(")
open('www/index.html','w').write(s)
print('built www/index.html',len(s))

