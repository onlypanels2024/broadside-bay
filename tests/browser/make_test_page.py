# Builds tests/browser/app-test.html from www/index.html, swapping real Firebase for the local stand-in.
s=open('www/index.html').read()
s=s.replace('<script src="vendor/firebase-app-compat.js"></script>\n<script src="vendor/firebase-auth-compat.js"></script>\n<script src="vendor/firebase-database-compat.js"></script>\n<script src="firebase-config.js"></script>',
 '<script src="./fakefirebase.js"></script>\n<script>window.BB_FIREBASE_CONFIG={apiKey:"fake"};</script>')
s=s.replace('src="vendor/','src="../../www/vendor/').replace('src="js/','src="../../www/js/').replace('url(fonts/','url(../../www/fonts/').replace("fetch(`snd/","fetch(`../../www/snd/")
s=s.replace("requestAnimationFrame(loop);\n})();","requestAnimationFrame(loop);\nwindow.__t={ev:c=>eval(c),get state(){return state},get enemies(){return enemies},P,NET,get gold(){return gold},get balls(){return balls},shoot:()=>{firing=true;setTimeout(()=>firing=false,150)},noAI:()=>{enemies.forEach(e=>{disposeGroup(e.g);scene.remove(e.bar)});enemies.length=0;popT=1e9;}};\n})();")
s=s.replace('</body>','<script>var module={exports:{}};</script><script src="../../functions/referee.js"></script><script>window.REF=module.exports;module={exports:{}};</script><script src="../../functions/economy.js"></script><script>window.ECO=module.exports;if(new URLSearchParams(location.search).get("referee"))document.write(\'<script src="./referee-shim.js"><\\/script>\');</script>\n</body>')
open('tests/browser/app-test.html','w').write(s)
