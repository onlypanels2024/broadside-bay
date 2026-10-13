// Firebase online play for Broadside Bay.
//  - Sign in with Google (progress saved online) or play as a guest with a chosen name (nothing saved).
//  - openRoom() exposes the small "room" interface the game uses (presence / peers / onConnection)
//    plus referee calls: reportHit, reportDeath, onReward, onBanned, serverNow.
(function () {
  'use strict';
  const PLAYER_KEYS = ['x', 'z', 'a', 'v', 'hp', 'mx', 'sh', 'lk', 'dw', 'fl', 'ti', 'cx', 'qc', 'du', 'rs', 'al', 'c', 'sg', 'dk', 'k', 'dn', 'kb', 's', 'm'];
  const cleanName = n => String(n || '').replace(/[^\p{L}\p{N} '_-]/gu, '').replace(/\s+/g, ' ').trim().slice(0, 16);

  function nativeAuth() {
    const cap = window.Capacitor;
    return cap && cap.isNativePlatform && cap.isNativePlatform() && cap.Plugins && cap.Plugins.FirebaseAuthentication || null;
  }

  window.BBFirebase = {
    cleanName,
    init(config) {
      if (!window.firebase || !config || !config.apiKey) return null;
      const app = firebase.apps.length ? firebase.app() : firebase.initializeApp(config);
      const auth = app.auth(), db = app.database();
      let guestName = '';
      const ready = new Promise(res => { const off = auth.onAuthStateChanged(() => { off(); res(); }); });

      const api = {
        ready, cleanName,
        user() {
          const u = auth.currentUser; if (!u) return null;
          const google = u.providerData.some(p => p.providerId === 'google.com');
          const name = google ? (cleanName((u.displayName || '').split(' ')[0]) || 'Captain') : guestName;
          return { uid: u.uid, google, name: name.length >= 2 ? name : 'Captain' };
        },
        async signInGoogle() {
          const plug = nativeAuth();
          if (plug) {
            const res = await plug.signInWithGoogle({ skipNativeAuth: true });
            const tok = res && res.credential && res.credential.idToken;
            if (!tok) throw new Error('Google sign-in was cancelled');
            await auth.signInWithCredential(firebase.auth.GoogleAuthProvider.credential(tok));
          } else {
            await auth.signInWithPopup(new firebase.auth.GoogleAuthProvider());
          }
          return api.user();
        },
        async signInGuest(name) {
          guestName = cleanName(name);
          if (guestName.length < 2) throw new Error('Pick a captain name of 2 to 16 letters or numbers');
          const u = auth.currentUser;
          if (!u || !u.isAnonymous) { if (u) await api.signOut(); await auth.signInAnonymously(); }
          return api.user();
        },
        async signOut() {
          const plug = nativeAuth(); if (plug) { try { await plug.signOut(); } catch (e) {} }
          await auth.signOut();
        },
        // Online progress lives in saves/<uid> and is written only by the referee.
        // Google captains keep the same uid on every phone; guests get a new one each launch.
        async loadSave() {
          const u = api.user(); if (!u) return null;
          try { return (await db.ref('saves/' + u.uid).get()).val(); } catch (e) { return null; }
        },
        // Ask the referee to do something. Returns the request's key (used to know when it's been dealt with).
        request(obj) {
          const u = auth.currentUser; if (!u) return null;
          const ref = db.ref('requests/' + u.uid).push();
          ref.set({ ...obj, t: firebase.database.ServerValue.TIMESTAMP }).catch(() => {});
          return ref.key;
        },
        // Follow the referee's copy of this captain's progress. Returns a function that stops following.
        watchSave(cb) {
          const u = auth.currentUser; if (!u) return () => {};
          const ref = db.ref('saves/' + u.uid), fn = s => cb(s.val());
          ref.on('value', fn); return () => ref.off('value', fn);
        },
        // Drawing checks need a signed-in user; anyone not signed in yet gets a quiet anonymous sign-in.
        async ensureUser() { await ready; if (!auth.currentUser) await auth.signInAnonymously(); return auth.currentUser.uid; },
        // The drawing checker's last health report (for showing why it's offline).
        async checkerStatus() { try { return (await db.ref('status/checker').get()).val(); } catch (e) { return null; } },
        // Top captains on a leaderboard: path 'board/w<week>' or 'board/all', sorted by field, best first.
        async board(path, field, n) {
          const out = [];
          try { const snap = await db.ref(path).orderByChild(field).limitToLast(n || 25).get(); snap.forEach(c => { out.push({ uid: c.key, ...c.val() }); }); } catch (e) { return null; }
          return out.reverse();
        },
        async boardMine(path) { const u = auth.currentUser; if (!u) return null; try { return (await db.ref(path + '/' + u.uid).get()).val(); } catch (e) { return null; } },
        // Follow the list of fleets. Returns a function that stops following.
        watchFleets(cb) { const ref = db.ref('fleets'), fn = s => cb(s.val() || {}); ref.on('value', fn); return () => ref.off('value', fn); },
        // The shared kraken: follow its health, and record a hit on it (health down one, my hit count up one).
        krakenWatch(slot, cb) { const ref = db.ref('kraken/' + slot + '/hp'), fn = s => cb(s.val()); ref.on('value', fn); return () => ref.off('value', fn); },
        krakenHit(slot) {
          const u = auth.currentUser; if (!u) return;
          db.ref('kraken/' + slot + '/hp').transaction(h => (h === null ? 59 : h > 0 ? h - 1 : undefined)).catch(() => {});
          db.ref('kraken/' + slot + '/hits/' + u.uid).transaction(n => (n || 0) + 1).catch(() => {});
        },
        // Friends: my list (uid -> name) and requests to me (uid -> {n}); both followed live.
        watchFriends(cb) {
          const u = auth.currentUser; if (!u) return () => {};
          const st = { list: {}, reqs: {} }, a = db.ref('friends/' + u.uid), b = db.ref('friendreq/' + u.uid);
          const fa = s => { st.list = s.val() || {}; cb(st); }, fb = s => { st.reqs = s.val() || {}; cb(st); };
          a.on('value', fa); b.on('value', fb); return () => { a.off('value', fa); b.off('value', fb); };
        },
        friendAsk(uid, myName) { const u = auth.currentUser; if (!u || uid === u.uid) return; db.ref('friendreq/' + uid + '/' + u.uid).set({ n: myName, t: firebase.database.ServerValue.TIMESTAMP }).catch(() => {}); },
        async friendAccept(uid, name, myName) { const u = auth.currentUser; if (!u) return;
          try { await db.ref('friends/' + u.uid + '/' + uid).set(String(name).slice(0, 16) || 'Captain'); await db.ref('friends/' + uid + '/' + u.uid).set(myName); await db.ref('friendreq/' + u.uid + '/' + uid).remove(); } catch (e) {} },
        async friendRemove(uid) { const u = auth.currentUser; if (!u) return; try { await db.ref('friends/' + u.uid + '/' + uid).remove(); await db.ref('friends/' + uid + '/' + u.uid).remove(); } catch (e) {} },
        // Duels: my inbox of challenges/acceptances; send one; clear one.
        duelWatch(cb) { const u = auth.currentUser; if (!u) return () => {}; const ref = db.ref('duelreq/' + u.uid), fn = s => cb(s.val() || {}); ref.on('value', fn); return () => ref.off('value', fn); },
        duelSend(uid, myName, ok) { const u = auth.currentUser; if (!u || uid === u.uid) return; const m = { n: myName, t: firebase.database.ServerValue.TIMESTAMP }; if (ok) m.ok = true; db.ref('duelreq/' + uid + '/' + u.uid).set(m).catch(() => {}); },
        duelClear(uid) { const u = auth.currentUser; if (!u) return; db.ref('duelreq/' + u.uid + '/' + uid).remove().catch(() => {}); },
        // Co-op Wave battle: invites (same shape as duel challenges) and the shared battle under coop/<host>.
        coopInboxWatch(cb) { const u = auth.currentUser; if (!u) return () => {}; const ref = db.ref('coopreq/' + u.uid), fn = s => cb(s.val() || {}); ref.on('value', fn); return () => ref.off('value', fn); },
        coopInvite(uid, myName, ok) { const u = auth.currentUser; if (!u || uid === u.uid) return; const m = { n: myName, t: firebase.database.ServerValue.TIMESTAMP }; if (ok) m.ok = true; db.ref('coopreq/' + uid + '/' + u.uid).set(m).catch(() => {}); },
        coopClear(uid) { const u = auth.currentUser; if (!u) return; db.ref('coopreq/' + u.uid + '/' + uid).remove().catch(() => {}); },
        coopSet(path, v) { if (!/^coop\//.test(path)) return; (v === null ? db.ref(path).remove() : db.ref(path).set(v)).catch(() => {}); },
        coopWatch(path, cb) { if (!/^coop\//.test(path)) return () => {}; const ref = db.ref(path), fn = s => cb(s.val()); ref.on('value', fn); return () => ref.off('value', fn); },
        // Report another captain's drawing to the referee.
        report(tg, dw) {
          const u = auth.currentUser; if (!u) return;
          db.ref('reports/' + u.uid).push({ tg: String(tg), dw, t: firebase.database.ServerValue.TIMESTAMP }).catch(() => {});
        },
        openRoom() { return openRoom(db, auth.currentUser.uid, () => api.user().name); },
      };
      return api;
    }
  };

  function openRoom(db, uid, getName) {
    let offset = 0, connected = false, mine = {}, others = new Map(), menuOnly = new Set(), snap = Object.freeze([]), dirty = true, closed = false;
    const connHandlers = [], rewardHandlers = [], bannedHandlers = [], offs = [];
    const listen = (ref, ev, fn) => { ref.on(ev, fn); offs.push(() => ref.off(ev, fn)); };
    listen(db.ref('.info/serverTimeOffset'), 'value', s => { offset = s.val() || 0; });
    listen(db.ref('.info/connected'), 'value', s => {
      connected = !!s.val(); connHandlers.forEach(h => h(connected));
      if (connected && !closed) {
        const on = db.ref('online/' + uid); on.onDisconnect().remove(); on.set(true).catch(() => {});
        db.ref('players/' + uid).onDisconnect().remove();
      }
    });
    const players = db.ref('players');
    const put = s => { if (s.key === uid) return; others.set(s.key, Object.freeze(s.val() || {})); dirty = true; };
    listen(players, 'child_added', put); listen(players, 'child_changed', put);
    listen(players, 'child_removed', s => { others.delete(s.key); dirty = true; });
    listen(db.ref('online'), 'value', s => { menuOnly = new Set(Object.keys(s.val() || {})); dirty = true; });
    listen(db.ref('rewards/' + uid), 'child_added', s => {
      const r = s.val(); s.ref.remove().catch(() => {});
      if (r && typeof r.g === 'number') rewardHandlers.forEach(h => h(r));
    });
    listen(db.ref('banned/' + uid), 'value', s => { if (s.val()) bannedHandlers.forEach(h => h()); });

    function rebuild() {
      const arr = [{ peer: uid, by: uid, isMe: true, sameTab: true, kind: 'viewer', guest: false, presence: Object.freeze({ ...mine }), updatedAt: Date.now() }];
      for (const [k, v] of others) arr.push({ peer: k, by: k, isMe: false, sameTab: false, kind: 'viewer', guest: false, presence: v, updatedAt: Date.now() });
      for (const k of menuOnly) if (k !== uid && !others.has(k)) arr.push({ peer: k, by: k, isMe: false, sameTab: false, kind: 'viewer', guest: false, presence: Object.freeze({ m: 'menu' }), updatedAt: Date.now() });
      snap = Object.freeze(arr); dirty = false;
    }

    let lastAtSea = false, writing = false;
    return {
      firebase: true, uid,
      serverNow: () => Date.now() + offset,
      connected: () => connected,
      onConnection(h) { connHandlers.push(h); setTimeout(() => h(connected)); return () => {}; },
      onPeers() { return () => {}; },
      peers() { if (dirty) rebuild(); return snap; },
      onlineIds() { return menuOnly; },
      async presence(patch) {
        if (closed) return;
        for (const k in patch) { if (patch[k] === null) delete mine[k]; else mine[k] = patch[k]; }
        dirty = true;
        const atSea = mine.m === 'open' && typeof mine.x === 'number';
        if (!atSea) { if (lastAtSea) { lastAtSea = false; await db.ref('players/' + uid).remove().catch(() => {}); } return; }
        if (writing) return; // never queue writes; the next tick sends fresh state
        const rec = { t: firebase.database.ServerValue.TIMESTAMP, n: getName() };
        for (const k of PLAYER_KEYS) if (mine[k] !== undefined && mine[k] !== null) rec[k] = mine[k];
        if (Array.isArray(rec.s) && !rec.s.length) delete rec.s;
        writing = true;
        try { await db.ref('players/' + uid).set(rec); lastAtSea = true; }
        catch (e) { /* refused by the rules (e.g. moved too fast); the next write sends fresh data */ }
        finally { writing = false; }
      },
      reportHit(shooter, sid, x, z, ti) {
        const h = { v: uid, s: String(shooter), sid: sid | 0, x: +x.toFixed(1), z: +z.toFixed(1), t: firebase.database.ServerValue.TIMESTAMP };
        if (typeof ti === 'number') h.ti = Math.round(ti);
        db.ref('hits').push(h).catch(() => {});
      },
      reportDeath() { db.ref('deaths').push({ v: uid, t: firebase.database.ServerValue.TIMESTAMP }).catch(() => {}); },
      onReward(h) { rewardHandlers.push(h); },
      onBanned(h) { bannedHandlers.push(h); },
      async close() {
        closed = true; offs.forEach(f => f());
        try { await db.ref('players/' + uid).remove(); await db.ref('online/' + uid).remove(); } catch (e) {}
      },
    };
  }
})();
