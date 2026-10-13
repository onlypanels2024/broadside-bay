// Asks the live referee to check two test drawings, exactly like a phone does, and reports what happened.
// Run by .github/workflows/checker-test.yml. Usage: node tools/checker-test.js <service-account.json> <out.txt>
const admin = require('../functions/node_modules/firebase-admin');
const fs = require('fs');
const [sa, out] = process.argv.slice(2);
admin.initializeApp({ credential: admin.credential.cert(require(sa)), databaseURL: 'https://overboard-2104-default-rtdb.europe-west1.firebasedatabase.app' });
const db = admin.database();
const enc = rows => { const b = rows.join('').split('').map(c => c === '#' ? 1 : 0); let h = ''; for (let k = 0; k < 64; k++) { let n = 0; for (let j = 0; j < 4; j++) n = n << 1 | b[k * 4 + j]; h += n.toString(16); } return h; };
const ANCHOR = enc(['................', '.......##.......', '......#..#......', '.......##.......', '....########....', '.......##.......', '.......##.......', '.......##.......', '.......##.......', '.......##.......', '.##....##....##.', '.###...##...###.', '..##...##...##..', '...##..##..##...', '....########....', '................']);
const FINGER = enc(['.......##.......', '......#..#......', '......#..#......', '......#..#......', '......#..#......', '......#..#......', '...##.#..#.##...', '..#..##..##..#..', '..#..#....#..#..', '..#..........#..', '..#..........#..', '..#..........#..', '...#........#...', '....#......#....', '.....######.....', '................']);
const UID = 'checker-test';
const log = []; const say = m => { console.log(m); log.push(m); };
async function check(name, dw) {
  const ref = db.ref(`requests/${UID}`).push();
  await ref.set({ k: 'check', dw, t: admin.database.ServerValue.TIMESTAMP });
  const t0 = Date.now();
  while (Date.now() - t0 < 90000) {
    const sv = (await db.ref(`saves/${UID}`).get()).val();
    if (sv && typeof sv.last === 'string' && sv.last >= ref.key) {
      const ok = !!(sv.dok && sv.dok[dw]);
      say(`${name}: ${ok ? 'ALLOWED' : 'REFUSED'} (${(sv.dchk && sv.dchk.dw === dw && sv.dchk.why) || '-'}) after ${((Date.now() - t0) / 1000).toFixed(1)} s`);
      return;
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  say(`${name}: no answer from the referee within 90 s`);
}
(async () => {
  await db.ref(`saves/${UID}`).remove();
  await check('anchor (should be allowed)', ANCHOR);
  await check('middle finger (should be refused)', FINGER);
  say('checker status: ' + JSON.stringify((await db.ref('status/checker').get()).val()));
  await db.ref(`saves/${UID}`).remove();
  await db.ref(`ref/reports`).child(ANCHOR).remove();
  fs.writeFileSync(out, log.join('\n') + '\n');
  process.exit(0);
})().catch(e => { say('test failed: ' + e.message); fs.writeFileSync(out, log.join('\n') + '\n'); process.exit(0); });
