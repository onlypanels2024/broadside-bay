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
        // drawings: same steps as functions/index.js checkFirst, with a stand-in for the AI
        const dw=typeof req.dw==='string'&&/^[0-9a-f]{64}$/.test(req.dw)?req.dw:null;
        if(dw&&(req.k==='check'||(req.k==='look'&&String(req.lk||'')[6]==='z'))){const cur=E.norm((await db.ref('saves/'+uid).get()).val());
          if(!(cur.dok&&cur.dok[dw])){let v;const bad=(await db.ref('ref/baddw/'+dw).get()).val();const ru=E.drawRules(dw);
            v=bad?{ok:false,why:'this drawing has been removed before'}:!ru.ok?ru:(window.__rude||[]).includes(dw)?{ok:false,why:'rude shape'}:{ok:true,why:'fine'};
            window.__refLog.push(['check',v.ok,v.why]);await new Promise(r=>setTimeout(r,800));
            await txn('saves/'+uid,sv=>E.applyCheck(sv,dw,v.ok,v.why,Date.now()));}}
        if(req.k==='check'){await txn('saves/'+uid,sv=>{const o=E.norm(sv);o.last=sv&&typeof sv.last==='string'&&sv.last>rid?sv.last:rid;return o;});continue;}
        const player=(await db.ref('players/'+uid).get()).val();let verdict;
        await txn('saves/'+uid,sv=>{verdict=E.processRequest(sv,req,player,Date.now());const out=verdict.save;
          out.last=sv&&typeof sv.last==='string'&&sv.last>rid?sv.last:rid;return out;});
        window.__refLog.push(['req',req.k,req.e||req.id||'',verdict.ok,verdict.reason||'']);}
    }while(again);}finally{busy=false;}}
  db.ref('requests').on('value',()=>{drain();});
  db.ref('reports').on('child_added',async s=>{const all=s.val()||{};const uid=s.key;await s.ref.remove();
    for(const rid in all){const rep=all[rid];const dw=rep.dw;await db.ref('ref/reports/'+dw+'/'+uid).set(Date.now());
      const count=Object.keys((await db.ref('ref/reports/'+dw).get()).val()||{}).length;
      const rude=count>=3||(window.__rudeOnReport||[]).includes(dw);window.__refLog.push(['report',rep.tg,count,rude]);
      if(!rude)continue;await db.ref('ref/baddw/'+dw).set({at:Date.now()});await txn('saves/'+rep.tg,sv=>sv?E.removeDrawing(sv,dw):sv);}});
})();
