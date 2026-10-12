// Runs the real referee logic (functions/referee.js + functions/economy.js) against the fake database,
// the same way functions/index.js does on Firebase.
(function(){
  const R=window.REF,E=window.ECO,db=window.__fakeDb;window.__refLog=[];
  const txn=async(path,fn)=>{const cur=(await db.ref(path).get()).val();const next=fn(cur);await db.ref(path).set(next);return next;};
  db.ref('hits').on('child_added',async s=>{const hit=s.val();await s.ref.remove();if(!hit)return;
    const shooter=(await db.ref('players/'+hit.s).get()).val(),victim=(await db.ref('players/'+hit.v).get()).val();
    const v=R.judgeHit(hit,shooter,victim,Date.now());window.__refLog.push(['hit',v.ok,v.reason||'']);
    if(!v.ok)return;await txn('ref/lives/'+hit.v,life=>R.addHit(life,hit));});
  db.ref('deaths').on('child_added',async s=>{const d=s.val();await s.ref.remove();if(!d)return;
    const life=(await db.ref('ref/lives/'+d.v).get()).val();await db.ref('ref/lives/'+d.v).remove();
    await txn('saves/'+d.v,sv=>E.applyDeath(sv));
    const v=R.judgeDeath(d,life,Date.now());window.__refLog.push(['death',!!v]);if(!v)return;
    const name=(await db.ref('players/'+d.v+'/n').get()).val()||'a captain';
    await txn('saves/'+v.killer,sv=>E.applyPvpKill(sv));
    await db.ref('rewards/'+v.killer).push({g:E.PVP.g,n:name,t:Date.now()});});
  // process every waiting request, one at a time, like the real referee does (one call per request)
  let busy=false,again=false;
  async function drain(){if(busy){again=true;return;}busy=true;
    try{do{again=false;const all=(await db.ref('requests').get()).val()||{};
      for(const uid of Object.keys(all))for(const rid of Object.keys(all[uid]||{}).sort()){
        const req=all[uid][rid];await db.ref('requests/'+uid+'/'+rid).remove();
        const player=(await db.ref('players/'+uid).get()).val();let verdict;
        await txn('saves/'+uid,sv=>{verdict=E.processRequest(sv,req,player,Date.now());const out=verdict.save;
          out.last=sv&&typeof sv.last==='string'&&sv.last>rid?sv.last:rid;return out;});
        window.__refLog.push(['req',req.k,req.e||req.id||'',verdict.ok,verdict.reason||'']);}
    }while(again);}finally{busy=false;}}
  db.ref('requests').on('value',()=>{drain();});
})();
