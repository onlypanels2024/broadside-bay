// Broadside Bay economy referee: the ONLY thing allowed to change online gold, XP, upgrades and ships.
// Phones send requests ("I sank a sloop", "buy Quick reload"); this decides what actually happens.
// Pure functions, no Firebase calls, so it can be unit-tested (and run in the browser test harness).
(function (root) {
  'use strict';
  const PORTS = [[0, 0], [175, -160], [-165, 175]];
  const SAFE_R = 30;
  const RANK_XP = [0, 250, 700, 1500, 3000, 5500, 9000];           // Deckhand .. Admiral
  const SHIPS = {
    brig: { rank: 1, price: 0, hull: 5 },
    corvette: { rank: 2, price: 800, hull: 7 },
    frigate: { rank: 3, price: 2000, hull: 9 },
    galleon: { rank: 5, price: 4500, hull: 12 },
    manowar: { rank: 7, price: 9000, hull: 15 },
  };
  const SHIP_ORDER = ['brig', 'corvette', 'frigate', 'galleon', 'manowar'];
  const UPGRADES = {
    broadside: { max: 1, price: () => 350 },
    reload: { max: 3, price: l => 140 + l * 110 },
    sails: { max: 3, price: l => 120 + l * 90 },
    hull: { max: 3, price: l => 150 + l * 120 },
    triple: { max: 1, price: () => 250 },
  };
  const REPAIR = 60;
  // Online, coins dropped by a sunk ship are included in the kill reward (pickups are just for show).
  const KILL = {
    sloop: { g: 70, xp: 20, pts: 1 },
    galleon: { g: 210, xp: 50, pts: 2.5 },
    boss: { g: 550, xp: 250, pts: 0 },
  };
  // How fast pirates can realistically be sunk: a bucket of 12 "sloop points" refilled at 8 per minute,
  // and at most one boss every 2 minutes (bosses appear every 4).
  const RATE = { cap: 12, perMin: 8, bossGapMs: 120000, maxRejects: 12, freshMs: 15000 };
  const PVP = { g: 150, xp: 120 };
  // Ship paint. A 7-letter code (hull, trim, sails, stripe, emblem colour, flag, emblem), each a base-36 index,
  // plus an optional 16x16 drawing (64 hex digits) when the emblem is the captain's own (index 35).
  // The rank needed for each choice; must match PAINT_RANK in the game (a test checks this).
  const PAINT_RANK = {"h":[1,1,1,1,1,2,2,3,4,5,6,7],"t":[1,1,1,1,1,2,2,3,4,5,6],"s":[1,1,1,1,2,3,4,4,5,6,7],"p":[1,1,1,1,2,2,3,4,5],"c":[1,1,1,1,2,3,3,4],"f":[1,1,1,1,2,2,3,4,5],"e":[1,1,1,1,2,2,3,3,4,4,5,7],"draw":2};
  const PAINT_SLOTS = 'htspcfe', DRAW_E = 35, LK_RE = /^[0-9a-z]{7}$/, DW_RE = /^[0-9a-f]{64}$/;

  const num = v => typeof v === 'number' && Number.isFinite(v);
  const inHarbour = (x, z) => num(x) && num(z) && PORTS.some(([px, pz]) => Math.hypot(x - px, z - pz) < SAFE_R);
  const rankIdx = xp => { let r = 0; RANK_XP.forEach((t, i) => { if (xp >= t) r = i; }); return r; };

  function fresh() {
    return { gold: 0, earned: 0, sunk: 0, xp: 0, up: { hull: 0, sails: 0, reload: 0, triple: 0, broadside: 0 }, ships: { brig: true }, ship: 'brig' };
  }
  function norm(s) {
    const f = fresh();
    if (!s || typeof s !== 'object') return f;
    const o = { ...f, ...s };
    for (const k of ['gold', 'earned', 'sunk', 'xp']) o[k] = num(o[k]) && o[k] >= 0 ? Math.floor(o[k]) : 0;
    o.up = { ...f.up };
    for (const k in f.up) { const v = s.up && s.up[k]; o.up[k] = num(v) ? Math.max(0, Math.min(UPGRADES[k].max, Math.floor(v))) : 0; }
    o.ships = { brig: true };
    if (s.ships && typeof s.ships === 'object') for (const k in s.ships) if (SHIPS[k] && s.ships[k] === true) o.ships[k] = true;
    o.ship = o.ships[s.ship] ? s.ship : 'brig';
    if (s.rl && typeof s.rl === 'object') o.rl = { ...s.rl }; else delete o.rl;
    const pt = s.paint && checkPaint(s.paint.lk, s.paint.dw, o.xp);
    if (pt) o.paint = pt; else delete o.paint;
    // drawings the checker has approved for this captain (newest last), and the last check's answer
    o.dok = {};
    if (s.dok && typeof s.dok === 'object') { const keys = Object.keys(s.dok).filter(k => DW_RE.test(k)).sort((a, b) => (s.dok[a] | 0) - (s.dok[b] | 0)).slice(-12); for (const k of keys) o.dok[k] = num(s.dok[k]) ? s.dok[k] : 1; }
    if (!Object.keys(o.dok).length) delete o.dok;
    if (s.dchk && typeof s.dchk === 'object' && DW_RE.test(s.dchk.dw || '')) o.dchk = { dw: s.dchk.dw, ok: !!s.dchk.ok, why: String(s.dchk.why || '').slice(0, 80), t: num(s.dchk.t) ? s.dchk.t : 0 }; else delete o.dchk;
    if (s.ck && typeof s.ck === 'object' && num(s.ck.n) && num(s.ck.t)) o.ck = { n: s.ck.n, t: s.ck.t }; else delete o.ck;
    return o;
  }
  // Is this paint allowed for a captain with this much XP? Returns the cleaned paint or null.
  function checkPaint(lk, dw, xp) {
    if (typeof lk !== 'string' || !LK_RE.test(lk)) return null;
    const rank = rankIdx(xp) + 1;
    for (let i = 0; i < 7; i++) {
      const k = PAINT_SLOTS[i], v = parseInt(lk[i], 36);
      const need = k === 'e' && v === DRAW_E ? PAINT_RANK.draw : PAINT_RANK[k][v];
      if (!need || need > rank) return null;
    }
    if (parseInt(lk[6], 36) === DRAW_E) { if (typeof dw !== 'string' || !DW_RE.test(dw)) return null; return { lk, dw }; }
    return { lk };
  }
  /*DRAWRULES*/function drawRules(dw){
  // Built-in check for well-known hate symbols in a 16x16 drawing (64 hex digits, row by row).
  // Backs up the AI check; the same code is in the game (a test keeps the two identical).
  if(typeof dw!=='string'||!/^[0-9a-f]{64}$/.test(dw))return{ok:false,why:'not a drawing'};
  const on=(x,y)=>x>=0&&y>=0&&x<16&&y<16&&((parseInt(dw[(y*16+x)>>2],16)>>(3-((y*16+x)&3)))&1)===1;
  let n=0;for(let i=0;i<256;i++)if(on(i&15,i>>4))n++;
  if(n<3)return{ok:false,why:'too empty'};
  for(let a=2;a<=7;a++)for(const th of [1,2])for(const mir of [1,-1]){
    if(a*th*2+th>16)continue;
    const cells=new Set(),c=a;
    const put=(x,y)=>{for(let i=0;i<th;i++)for(let j=0;j<th;j++)cells.add(((mir>0?x:2*a-x)*th+i)+','+(y*th+j));};
    for(let k=-a;k<=a;k++){put(c,c+k);put(c+k,c);}
    for(let k=0;k<=a;k++){put(c+k,c-a);put(c+a,c+k);put(c-k,c+a);put(c-a,c-k);}
    const size=(2*a+1)*th;
    for(let oy=0;oy+size<=16;oy++)for(let ox=0;ox+size<=16;ox++){
      let miss=0,extra=0;
      for(let y=0;y<size;y++)for(let x=0;x<size;x++){const want=cells.has(x+','+y),got=on(ox+x,oy+y);if(want&&!got)miss++;if(!want&&got)extra++;}
      if(miss<=(a>=4?1:0)&&extra<=Math.max(1,Math.floor((size*size-cells.size)*.06)))return{ok:false,why:'hate symbol'};
    }
  }
  return{ok:true};
}/*ENDDRAWRULES*/
  const docked = p => !!p && inHarbour(p.x, p.z);
  const atSea = (p, now) => !!p && p.al === 1 && num(p.t) && now - p.t <= RATE.freshMs && !inHarbour(p.x, p.z);

  // req = {k:'kill'|'up'|'repair'|'ship'|'look'|'reset', e?, id?, lk?, dw?}; player = this captain's /players record (or null)
  // Returns {save, ok, reason, strike}
  function processRequest(saveIn, req, player, now) {
    const s = norm(saveIn);
    const no = (reason, strike) => ({ save: s, ok: false, reason, strike: !!strike });
    if (!req || typeof req.k !== 'string') return no('malformed');
    switch (req.k) {
      case 'kill': {
        const K = KILL[req.e];
        if (!K) return no('unknown ship type');
        if (!atSea(player, now)) return no('not at sea');
        const rl = s.rl ? { ...s.rl } : { b: RATE.cap, t: now, lb: 0, rj: 0 };
        rl.b = Math.min(RATE.cap, (num(rl.b) ? rl.b : RATE.cap) + Math.max(0, now - (num(rl.t) ? rl.t : now)) / 60000 * RATE.perMin);
        rl.t = now;
        const reject = reason => {
          rl.rj = (rl.rj | 0) + 1; const strike = rl.rj >= RATE.maxRejects; if (strike) rl.rj = 0;
          s.rl = rl; return no(reason, strike);
        };
        if (req.e === 'boss') { if (now - (rl.lb || 0) < RATE.bossGapMs) return reject('boss claimed too soon'); rl.lb = now; }
        else { if (rl.b < K.pts) return reject('sinking faster than pirates appear'); rl.b -= K.pts; }
        rl.rj = 0; s.rl = rl;
        s.gold += K.g; s.earned += K.g; s.xp += K.xp; s.sunk += 1;
        return { save: s, ok: true };
      }
      case 'up': {
        const U = UPGRADES[req.id];
        if (!U) return no('unknown upgrade');
        if (!docked(player)) return no('not in harbour');
        const lvl = s.up[req.id];
        if (lvl >= U.max) return no('already fitted');
        const price = U.price(lvl);
        if (s.gold < price) return no('not enough gold');
        s.gold -= price; s.up[req.id] = lvl + 1;
        return { save: s, ok: true };
      }
      case 'repair': {
        if (!docked(player)) return no('not in harbour');
        if (s.gold < REPAIR) return no('not enough gold');
        s.gold -= REPAIR; return { save: s, ok: true };
      }
      case 'ship': {
        const S = SHIPS[req.id];
        if (!S) return no('unknown ship');
        // switching to a ship you already own: in harbour, or before setting sail (from the main menu)
        if (s.ships[req.id]) { if (atSea(player, now)) return no('not in harbour'); s.ship = req.id; return { save: s, ok: true }; }
        if (!docked(player)) return no('not in harbour');
        if (rankIdx(s.xp) + 1 < S.rank) return no('rank too low');
        if (s.gold < S.price) return no('not enough gold');
        s.gold -= S.price; s.ships[req.id] = true; s.ship = req.id;
        return { save: s, ok: true };
      }
      case 'look': {
        const pt = checkPaint(req.lk, req.dw, s.xp);
        if (!pt) return no('paint not unlocked');
        if (pt.dw && !(s.dok && s.dok[pt.dw])) return no('drawing not approved');
        s.paint = pt; return { save: s, ok: true };
      }
      case 'reset': {
        const f = fresh(); if (s.rl) f.rl = s.rl;   // keep the rate limiter so a reset can't be used to farm
        const pt = s.paint && checkPaint(s.paint.lk, s.paint.dw, 0); if (pt) f.paint = pt;   // keep colours a Deckhand may use
        return { save: f, ok: true };
      }
      default: return no('unknown request');
    }
  }
  // Drawing checks cost a little money (AI), so each captain gets CHECKS.perHour of them.
  const CHECKS = { perHour: 15 };
  function checkQuota(saveIn, now) {
    const s = norm(saveIn); const ck = s.ck && now - s.ck.t < 3600000 ? { ...s.ck } : { n: 0, t: now };
    if (ck.n >= CHECKS.perHour) return { save: s, ok: false };
    ck.n++; s.ck = ck; return { save: s, ok: true };
  }
  // Record the checker's answer; approved drawings may then be used as an emblem.
  function applyCheck(saveIn, dw, ok, why, now) {
    const s = norm(saveIn);
    s.dchk = { dw, ok: !!ok, why: String(why || '').slice(0, 80), t: now };
    if (ok) { s.dok = { ...(s.dok || {}), [dw]: now }; const k = Object.keys(s.dok).sort((a, b) => s.dok[a] - s.dok[b]); while (k.length > 12) delete s.dok[k.shift()]; }
    return s;
  }
  // A drawing was found to be rude after all (reports): take it off the ship and out of the approved list.
  function removeDrawing(saveIn, dw) {
    const s = norm(saveIn);
    if (s.dok) { delete s.dok[dw]; if (!Object.keys(s.dok).length) delete s.dok; }
    if (s.paint && s.paint.dw === dw) s.paint = { lk: s.paint.lk.slice(0, 6) + '1' };
    return s;
  }
  // A captain sank: they lose half the gold in their hold.
  function applyDeath(saveIn) { const s = norm(saveIn); s.gold -= Math.floor(s.gold / 2); return s; }
  // A captain sank another captain (already confirmed by the hit referee).
  function applyPvpKill(saveIn) { const s = norm(saveIn); s.gold += PVP.g; s.earned += PVP.g; s.xp += PVP.xp; s.sunk += 1; return s; }

  const api = { processRequest, applyDeath, applyPvpKill, fresh, norm, rankIdx, inHarbour, checkPaint, drawRules, checkQuota, applyCheck, removeDrawing, CHECKS, PAINT_RANK, SHIPS, SHIP_ORDER, UPGRADES, KILL, RATE, PVP, RANK_XP, REPAIR };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ECONOMY = api;
})(typeof self !== 'undefined' ? self : this);
