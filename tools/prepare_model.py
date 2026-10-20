"""Prepare a 3D model (.glb, e.g. from TRELLIS) for the game, before it is ever loaded.

  python3 tools/prepare_model.py IN.glb www/models/NAME.glb

What it does (and prints):
  - removes any lights or cameras baked into the file (these washed every ship and island white once)
  - turns off any glow (emissive) and sets a plain, non-mirror finish so it matches the game's lighting
  - re-saves the skin as a 1024px JPEG to shrink the file
  - reports triangles, size and any warnings
"""
import sys, json, struct, io
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
assert d[:4] == b'glTF', 'not a .glb file'
jl = struct.unpack('<I', d[12:16])[0]
j = json.loads(d[20:20 + jl])
binc = d[20 + jl:]
bl = struct.unpack('<I', binc[:4])[0]
blob = bytearray(binc[8:8 + bl])
warn = []

# 1. lights and cameras
ext = j.get('extensions', {})
nl = len(ext.get('KHR_lights_punctual', {}).get('lights', []))
ext.pop('KHR_lights_punctual', None)
if not ext: j.pop('extensions', None)
j['extensionsUsed'] = [e for e in j.get('extensionsUsed', []) if e != 'KHR_lights_punctual']
if not j['extensionsUsed']: j.pop('extensionsUsed')
nc = len(j.pop('cameras', []))
for n in j.get('nodes', []):
    n.pop('camera', None)
    if 'extensions' in n:
        n['extensions'].pop('KHR_lights_punctual', None)
        if not n['extensions']: n.pop('extensions')
if nl or nc: warn.append(f'removed {nl} built-in lights and {nc} cameras')

# 2. materials: no glow, plain finish
for m in j.get('materials', []):
    if m.get('emissiveFactor') and any(m['emissiveFactor']): warn.append('removed glow from material'); 
    m.pop('emissiveFactor', None); m.pop('emissiveTexture', None)
    pbr = m.setdefault('pbrMetallicRoughness', {})
    pbr['metallicFactor'] = min(pbr.get('metallicFactor', 1), 0.35)
    pbr['roughnessFactor'] = max(pbr.get('roughnessFactor', 1), 0.5)

# 3. re-save textures as 1024px JPEG
newblob = bytearray(); views = j['bufferViews']; remap = {}
img_views = {im['bufferView'] for im in j.get('images', []) if 'bufferView' in im}
for i, v in enumerate(views):
    data = bytes(blob[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])
    if i in img_views:
        im = Image.open(io.BytesIO(data)).convert('RGB')
        if max(im.size) > 1024: im = im.resize((1024, 1024), Image.LANCZOS)
        out = io.BytesIO(); im.save(out, 'JPEG', quality=88); data = out.getvalue()
    while len(newblob) % 4: newblob += b'\0'
    v['byteOffset'] = len(newblob); v['byteLength'] = len(data); newblob += data
for im in j.get('images', []):
    if 'bufferView' in im: im['mimeType'] = 'image/jpeg'
while len(newblob) % 4: newblob += b'\0'
j['buffers'] = [{'byteLength': len(newblob)}]

# 4. report
tris = 0
for mesh in j.get('meshes', []):
    for p in mesh['primitives']:
        a = j['accessors'][p['indices']] if 'indices' in p else j['accessors'][p['attributes']['POSITION']]
        tris += a['count'] // 3
if tris > 40000: warn.append(f'{tris} triangles is heavy for phones (aim under 40,000)')

js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(newblob)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(newblob), 0x004E4942) + bytes(newblob)
open(dst, 'wb').write(out)
print(f'{dst}: {tris} triangles, {len(d)/1e6:.2f} MB -> {len(out)/1e6:.2f} MB')
for w in warn: print(' -', w)
