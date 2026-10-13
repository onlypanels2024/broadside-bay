// Minimal stand-in for the Firebase compat SDK (auth + realtime database), shared between tabs
// through BroadcastChannel. Only for local testing of Broadside Bay's online play.
(function(){
  const bc=new BroadcastChannel('fakefb');let tree={};const listeners=[];
  const parts=p=>String(p||'').split('/').filter(Boolean);
  const getAt=p=>{let n=tree;for(const k of parts(p)){if(n==null||typeof n!=='object')return null;n=n[k];}return n===undefined?null:n;};
  const fix=v=>{if(v&&typeof v==='object'){if(v['.sv']==='timestamp')return Date.now();const o=Array.isArray(v)?[]:{};for(const k in v){const x=fix(v[k]);if(x!==null&&x!==undefined)o[k]=x;}return Object.keys(o).length?o:null;}return v;};
  function setAt(p,v,remote){const ks=parts(p);v=fix(v);if(!ks.length){tree=v||{};}else{let n=tree;for(let i=0;i<ks.length-1;i++){if(!n[ks[i]]||typeof n[ks[i]]!=='object')n[ks[i]]={};n=n[ks[i]];}
      if(v===null||v===undefined)delete n[ks[ks.length-1]];else n[ks[ks.length-1]]=JSON.parse(JSON.stringify(v));}
    if(!remote)bc.postMessage({p,v});fire();}
  bc.onmessage=e=>{if(e.data.sync){bc.postMessage({full:tree});return;}if(e.data.full){if(!Object.keys(tree).length){tree=e.data.full;fire();}return;}setAt(e.data.p,e.data.v,true);};
  bc.postMessage({sync:1});
  const snap=(key,val,path)=>({key,val:()=>val===undefined?null:JSON.parse(JSON.stringify(val)),ref:ref(path),exists:()=>val!=null});
  function fire(){for(const L of listeners){const v=getAt(L.path);
    if(L.ev==='value'){const j=JSON.stringify(v);if(j!==L.last){L.last=j;L.fn(snap(parts(L.path).pop(),v,L.path));}continue;}
    const cur=(v&&typeof v==='object')?v:{};const prev=L.prev||{};
    for(const k in cur){const j=JSON.stringify(cur[k]);if(!(k in prev)){if(L.ev==='child_added')L.fn(snap(k,cur[k],L.path+'/'+k));}else if(prev[k]!==j&&L.ev==='child_changed')L.fn(snap(k,cur[k],L.path+'/'+k));}
    for(const k in prev)if(!(k in cur)&&L.ev==='child_removed')L.fn(snap(k,null,L.path+'/'+k));
    const np={};for(const k in cur)np[k]=JSON.stringify(cur[k]);L.prev=np;}}
  let pushN=0;
  function ref(path){path=parts(path).join('/');return{
    key:parts(path).pop()||null,
    on(ev,fn){if(path==='.info/serverTimeOffset'){setTimeout(()=>fn(snap('x',0)));return fn;}if(path==='.info/connected'){setTimeout(()=>fn(snap('c',true)));return fn;}
      const L={path,ev,fn};if(ev!=='value'){L.prev={};}listeners.push(L);
      const v=getAt(path);if(ev==='value'){L.last=JSON.stringify(v);setTimeout(()=>fn(snap(parts(path).pop(),v,path)));}
      else{const cur=(v&&typeof v==='object')?v:{};const np={};for(const k in cur){np[k]=JSON.stringify(cur[k]);if(ev==='child_added')setTimeout(()=>fn(snap(k,cur[k],path+'/'+k)));}L.prev=np;}return fn;},
    off(ev,fn){const i=listeners.findIndex(L=>L.path===path&&L.ev===ev&&L.fn===fn);if(i>=0)listeners.splice(i,1);},
    async set(v){setAt(path,v);},async remove(){setAt(path,null);},async update(o){for(const k in o)setAt(path+'/'+k,o[k]);},
    push(v){const k='p'+Date.now().toString(36).padStart(9,'0')+String(pushN++).padStart(6,'0')+Math.random().toString(36).slice(2,6);const r=ref(path+'/'+k);if(v===undefined)return r;const pr=r.set(v);pr.key=k;return pr;},
    async get(){return snap(parts(path).pop(),getAt(path),path);},
    orderByChild(f){return{limitToLast(n){return{async get(){const v=getAt(path)||{};const arr=Object.entries(v).filter(([k,x])=>x&&typeof x[f]==='number').sort((a,b)=>a[1][f]-b[1][f]).slice(-n);
      return{val:()=>Object.fromEntries(arr),forEach(fn){arr.forEach(([k,x])=>fn({key:k,val:()=>x}));}};}};}};},
    onDisconnect(){return{remove(){},set(){}}},
    child(c){return ref(path+'/'+c);}}}
  const db={ref};
  const who=new URLSearchParams(location.search).get('who')||'guest';
  let user=null;const authCbs=[];
  const setUser=u=>{user=u;authApi.currentUser=u;authCbs.forEach(cb=>cb(u));};
  const authApi={currentUser:null,onAuthStateChanged(cb){authCbs.push(cb);setTimeout(()=>cb(user));return()=>{const i=authCbs.indexOf(cb);if(i>=0)authCbs.splice(i,1);};},
    async signInAnonymously(){setUser({uid:'anon_'+Math.random().toString(36).slice(2,8),isAnonymous:true,providerData:[],displayName:null});return{user};},
    async signInWithPopup(){setUser({uid:'google_'+who,isAnonymous:false,providerData:[{providerId:'google.com'}],displayName:'Gary Falzon'});return{user};},
    async signInWithCredential(){return authApi.signInWithPopup();},async signOut(){setUser(null);}};
  const app={auth:()=>authApi,database:()=>db};
  const fb={apps:[],initializeApp(){fb.apps.push(app);return app;},app:()=>app,database:{ServerValue:{TIMESTAMP:{'.sv':'timestamp'}}},auth:{GoogleAuthProvider:class{static credential(t){return{t}}}}};
  window.firebase=fb;window.__fakeTree=()=>tree;window.__fakeDb=db;
})();
