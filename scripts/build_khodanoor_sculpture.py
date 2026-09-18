"""Simple interpretive seated memorial from the supplied drawing. No facial detail."""
import bpy, math
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parents[1]/'outputs/khaneh-portraits/assets/sculpture'
bpy.ops.wm.read_factory_settings(use_empty=True)
mat=bpy.data.materials.new('White plaster');mat.diffuse_color=(.9,.9,.88,1)
def finish(obj,name):
    obj.name='Khodanoor / '+name;obj.data.materials.append(mat)
    if obj.type=='MESH':
        for face in obj.data.polygons:face.use_smooth=True
    return obj
def oval(name,center,scale):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=center)
    obj=bpy.context.object;obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(obj,name)
def limb(name,a,b,radius,depth=None):
    a,b=Vector(a),Vector(b);o=oval(name,(a+b)/2,(radius,depth or radius,(b-a).length*.5+radius*.5))
    o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o
def cord(name,points,radius):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3
    s=curve.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);return finish(o,name)
# Body on the right, facing left. A bowed head and round tunic carry the gesture.
oval('seated tunic',(.35,.02,.32),(.24,.23,.31))
limb('curved torso',(.40,.01,.4),(.16,.02,.91),.205,.19)
oval('shoulders',(.17,.02,.86),(.205,.22,.17))
limb('neck',(.09,0,.93),(.01,-.015,1.02),.075)
head=oval('bowed head',(-.025,-.025,1.055),(.14,.135,.175));head.rotation_euler.y=-.38
oval('simple hair mass',(-.012,.004,1.115),(.145,.14,.12))
# Raised knees, loose trousers and bare feet, without pockets or stitching.
for side,y in [('near',-.19),('far',.17)]:
    knee=(-.10,y,.64 if side=='near' else .70)
    limb(side+' upper trouser',(.31,y*.65,.29),knee,.135,.12)
    limb(side+' lower trouser',knee,(-.30,y,.12),.092,.105)
    oval(side+' bare foot',(-.43,y-.015,.07),(.17,.078,.055))
# Sleeves reach toward the pole; hands sit together on its left side.
limb('near upper sleeve',(.19,-.19,.87),(.04,-.29,.57),.102)
limb('near fore sleeve',(.04,-.29,.57),(-.40,-.27,.40),.078)
oval('near hand',(-.49,-.255,.36),(.084,.048,.067))
limb('far upper sleeve',(.13,.19,.87),(-.10,.21,.57),.095)
limb('far fore sleeve',(-.10,.21,.57),(-.42,.09,.40),.065)
oval('far hand',(-.49,.035,.37),(.08,.046,.064))
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.041,depth=1.75,location=(-.38,-.065,.875))
finish(bpy.context.object,'pole')
cord('restraint',[(-.48,-.27,.41),(-.34,-.25,.44),(-.32,.015,.44),(-.48,.07,.41)],.012)
cord('restraint return',[(-.48,.07,.41),(-.43,-.06,.45),(-.48,-.27,.41)],.010)
# Explicit selection excludes future studio helpers from the asset.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(root/'khodanoor-seated-white.glb'),export_format='GLB',use_selection=True,export_yup=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'khodanoor-seated-white.blend'))
print('KHODANOOR_SCULPTURE_SAVED')
