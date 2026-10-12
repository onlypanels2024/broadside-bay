// Checks a captain's own emblem drawing (16x16, 64 hex digits) with Google's Gemini AI on Vertex AI,
// billed to this Firebase project. Used before a drawing can go on a ship, and again when one is reported.
const zlib = require('zlib');
const admin = require('firebase-admin');

// Newest first; if one isn't available in this project the next is tried.
const MODELS = ['gemini-3.1-flash-lite', 'gemini-3-flash', 'gemini-2.5-flash'];

const bit = (dw, i) => (parseInt(dw[i >> 2], 16) >> (3 - (i & 3))) & 1;

function crc32(buf) {
  let c, crc = 0xffffffff;
  for (let n = 0; n < buf.length; n++) {
    c = (crc ^ buf[n]) & 0xff;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return (crc ^ 0xffffffff) >>> 0;
}
// The drawing as a black-on-white PNG, each square 16x16 pixels with a white border.
function drawingPng(dw) {
  const cell = 16, pad = 32, size = 16 * cell + pad * 2;
  const raw = Buffer.alloc((size + 1) * size, 255);
  for (let y = 0; y < size; y++) {
    raw[y * (size + 1)] = 0;
    for (let x = 0; x < size; x++) {
      const gx = Math.floor((x - pad) / cell), gy = Math.floor((y - pad) / cell);
      if (gx >= 0 && gy >= 0 && gx < 16 && gy < 16 && bit(dw, gy * 16 + gx)) raw[y * (size + 1) + 1 + x] = 0;
    }
  }
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td));
    return Buffer.concat([len, td, crc]);
  };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(size, 0); ihdr.writeUInt32BE(size, 4); ihdr[8] = 8; ihdr[9] = 0;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}
const asText = dw => Array.from({ length: 16 }, (_, y) => Array.from({ length: 16 }, (_, x) => bit(dw, y * 16 + x) ? '#' : '.').join('')).join('\n');

function prompt(dw, reported) {
  return `You check emblems that players draw for a family-friendly pirate ship game (players may be 12+).
A player drew this 16x16 pixel picture to show on their ship's sails and flag. It is shown as an image and as a grid ('#' = filled):

${asText(dw)}

${reported ? 'Another player has REPORTED this drawing as rude, so look carefully, including at what the shape could represent.' : ''}
Mark it rude if it shows or clearly suggests any of: genitals, breasts or sexual acts; an obscene gesture (such as a raised middle finger);
a hate symbol (such as a swastika, SS runes, or symbols of hate groups); slurs, swear words or rude words/letters; drugs; gore.
Pirate things (skulls, crossbones, swords, cannons, ships, anchors), faces, animals, hearts, stars, letters, initials, numbers and abstract shapes are fine.
Answer only with JSON: {"rude": true or false, "what": "a few words saying what it looks like"}`;
}

let workingModel = null;
async function aiCheck(dw, reported) {
  const project = process.env.GCLOUD_PROJECT || process.env.GOOGLE_CLOUD_PROJECT || 'overboard-2104';
  const token = (await admin.credential.applicationDefault().getAccessToken()).access_token;
  const body = {
    contents: [{ role: 'user', parts: [{ inlineData: { mimeType: 'image/png', data: drawingPng(dw).toString('base64') } }, { text: prompt(dw, reported) }] }],
    generationConfig: { temperature: 0, maxOutputTokens: 200, responseMimeType: 'application/json' },
  };
  let lastErr = null;
  for (const model of workingModel ? [workingModel] : MODELS) {
    const url = `https://aiplatform.googleapis.com/v1/projects/${project}/locations/global/publishers/google/models/${model}:generateContent`;
    const res = await fetch(url, { method: 'POST', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (res.status === 404) { lastErr = new Error(model + ' not available'); continue; }
    if (!res.ok) throw new Error('AI ' + res.status + ': ' + (await res.text()).slice(0, 300));
    const out = await res.json();
    // Google's own safety filter refusing to even look at it counts as rude
    const c0 = (out.candidates || [])[0] || {};
    if ((out.promptFeedback && out.promptFeedback.blockReason) || c0.finishReason === 'SAFETY' || c0.finishReason === 'PROHIBITED_CONTENT') { workingModel = model; return { rude: true, what: 'blocked by safety filter', model }; }
    const text = ((((out.candidates || [])[0] || {}).content || {}).parts || []).map(p => p.text || '').join('');
    const m = text.match(/\{[\s\S]*\}/);
    if (!m) throw new Error('AI gave no answer: ' + text.slice(0, 200));
    const j = JSON.parse(m[0]);
    workingModel = model;
    return { rude: j.rude === true, what: String(j.what || '').slice(0, 60), model };
  }
  throw lastErr || new Error('no AI model available');
}

module.exports = { aiCheck, drawingPng, asText, MODELS };
