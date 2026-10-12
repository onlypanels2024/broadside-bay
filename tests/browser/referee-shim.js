// Runs the real referee logic (functions/referee.js) against the fake database, like functions/index.js does on Firebase.
(function(){
  const R=window.REF,db=window.__fakeDb;window.__refLog=[];
  db.ref('hits').on('child_added',async s=>{const hit=s.val();await s.ref.remove();if(!hit)return;
    const shooter=(await db.ref('players/'+hit.s).get()).val(),victim=(await db.ref('players/'+hit.v).get()).val();
    const v=R.judgeHit(hit,shooter,victim,Date.now());window.__refLog.push(['hit',v.ok,v.reason||'']);
    if(!v.ok)return;const life=(await db.ref('ref/lives/'+hit.v).get()).val();await db.ref('ref/lives/'+hit.v).set(R.addHit(life,hit));});
  db.ref('deaths').on('child_added',async s=>{const d=s.val();await s.ref.remove();if(!d)return;
    const life=(await db.ref('ref/lives/'+d.v).get()).val();await db.ref('ref/lives/'+d.v).remove();
    const v=R.judgeDeath(d,life,Date.now());window.__refLog.push(['death',!!v]);if(!v)return;
    const name=(await db.ref('players/'+d.v+'/n').get()).val()||'a captain';
    await db.ref('rewards/'+v.killer).push({g:v.reward,n:name,t:Date.now()});});
})();
