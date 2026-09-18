"""Export a separate point study; never overwrite the source GLB or Blender file.
Run: blender --background --python scripts/sample_sculpture_particles.py
"""
import bpy, random, math, bisect, json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'outputs/khaneh-portraits/assets/sculpture'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root / 'hamid-carrying-white.glb'))
rng = random.Random(2026)
triangles, cumulative = [], []
total = 0
for obj in bpy.context.scene.objects:
    name = obj.name.lower()
    if obj.type != 'MESH' or any(word in name for word in
            ('plinth', 'brow', 'eyelid', 'lip', 'nose', 'nostril', 'hair lock', 'lace', 'seam', 'zipper', 'knuckle')):
        continue
    mesh = obj.data
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
points = []
for i in range(48000):
    a, b, c, normal, detail = triangles[bisect.bisect_left(cumulative, rng.random()*total)]
    u, v = math.sqrt(rng.random()), rng.random()
    p = (1-u)*a + u*(1-v)*b + u*v*c
    # Most points stay on the surface; the outer population falls off exponentially.
    halo = i % 8 == 0
    spread = min(.48, rng.expovariate(13)) if halo else 0
    p += normal * spread
    # Blender Z-up -> browser Y-up, centered on the figure.
    points.extend(round(x, 5) for x in (p.x+.1, p.z-1.12, -p.y,
                  normal.x, normal.z, -normal.y, rng.random(), spread))
output = root / 'hamid-particles.json'
output.write_text(json.dumps({'count':48000, 'stride':8, 'points':points,
    'description':'Interpretive sculpture surface, detail-weighted sampling with a sparse outer cloud.'}, separators=(',', ':')))
print('PARTICLES_EXPORTED', output, output.stat().st_size)
