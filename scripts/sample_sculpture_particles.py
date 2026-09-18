"""Export a separate point study; never overwrite the source GLB or Blender file.
Run: blender --background --python scripts/sample_sculpture_particles.py
"""
import bpy, random, math, bisect, json, hashlib, sys
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1] / 'outputs/khaneh-portraits/assets/sculpture'
person = 'khodanoor' if '--khodanoor' in sys.argv else 'hamid'
source = root / ('khodanoor-seated-white.blend' if person=='khodanoor' else 'hamid-carrying-white.blend')
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
depsgraph = bpy.context.evaluated_depsgraph_get()
rng = random.Random(2026)
triangles, cumulative = [], []
total = 0
for obj in bpy.context.scene.objects:
    name = obj.name.lower()
    if obj.type not in ('MESH', 'CURVE') or obj.hide_render or not name.startswith(('carrier', 'passenger', 'khodanoor')) or any(word in name for word in
            ('plinth', 'brow', 'eye', 'lip', 'nose', 'nostril', 'hair strand', 'mouth', 'finger division', 'supporting fingers', 'lace', 'seam', 'stitch', 'zipper', 'knuckle', 'pocket', 'belt loop', 'fold', 'wrinkle', 'sleeve band', 'drawstring')):
        continue
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    detail = any(word in name for word in ('hand', 'hood', 'head', 'torso'))
    for tri in mesh.loop_triangles:
        a, b, c = [obj.matrix_world @ mesh.vertices[i].co for i in tri.vertices]
        cross = (b-a).cross(c-a)
        area = cross.length / 2
        if area < 1e-12:
            continue
        total += area * (1.6 if detail else 1)
        cumulative.append(total)
        triangles.append((a, b, c, cross.normalized(), detail))
    evaluated.to_mesh_clear()
if not triangles:
    raise RuntimeError('No carrier or passenger geometry found in saved Blender file')
# Fit updated proportions without changing the source sculpture.
minimum = [min(p[axis] for tri in triangles for p in tri[:3]) for axis in range(3)]
maximum = [max(p[axis] for tri in triangles for p in tri[:3]) for axis in range(3)]
center = [(a+b)/2 for a,b in zip(minimum, maximum)]
scale = 2.15 / max(maximum[i]-minimum[i] for i in range(3))
points = []
for i in range(48000):
    a, b, c, normal, detail = triangles[bisect.bisect_left(cumulative, rng.random()*total)]
    u, v = math.sqrt(rng.random()), rng.random()
    p = (1-u)*a + u*(1-v)*b + u*v*c
    # Most points stay on the surface; the outer population falls off exponentially.
    halo = i % 8 == 0
    spread = min(.48, rng.expovariate(13)) if halo else 0
    p = (p - Vector(center)) * scale + normal * spread
    # Blender Z-up -> browser Y-up, centered on the figure.
    points.extend(round(x, 5) for x in (p.x, p.z, -p.y,
                  normal.x, normal.z, -normal.y, rng.random(), spread))
output = root / (person+'-particles.json')
output.write_text(json.dumps({'count':48000, 'stride':8, 'points':points,
    'source':source.name, 'sourceSha256':source_hash,
    'description':'Interpretive sculpture surface, detail-weighted sampling with a sparse outer cloud.'}, separators=(',', ':')))
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash, 'Source changed during export'
print('PARTICLES_EXPORTED', output, output.stat().st_size)
