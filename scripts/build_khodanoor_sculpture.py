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
# One continuous long garment, from shoulders to a broad seated hem.
# Vertical panels cover the hips instead of a separate spherical pelvis.
profiles=[(.065,.22,.35,.275),(.09,.24,.38,.29),(.17,.25,.38,.29),
          (.34,.28,.33,.27),(.53,.26,.285,.24),(.73,.20,.24,.22),
          (.87,.15,.20,.20),(.94,.085,.12,.13),(.97,.06,.075,.09)]
vertices=[];faces=[];sides=64
for z,x,rx,ry in profiles:
    for j in range(sides):
        angle=2*math.pi*j/sides
        # A few broad cloth undulations, no stitching or small accessories.
        ripple=1+.025*math.cos(6*angle)*(1-z)
        vertices.append((x+rx*math.cos(angle)*ripple,.02+ry*math.sin(angle)*ripple,z))
for i in range(len(profiles)-1):
    for j in range(sides):
        a=i*sides+j;b=i*sides+(j+1)%sides
        faces.append((a,b,b+sides,a+sides))
faces.append(tuple(reversed(range(sides))))
faces.append(tuple((len(profiles)-1)*sides+j for j in range(sides)))
mesh=bpy.data.meshes.new('Continuous tunic surface');mesh.from_pydata(vertices,[],faces);mesh.update()
garment=bpy.data.objects.new('Long tunic',mesh);bpy.context.collection.objects.link(garment)
finish(garment,'long draped tunic')
modifier=garment.modifiers.new('Soft cloth silhouette','SUBSURF');modifier.levels=2
bpy.context.view_layer.objects.active=garment
bpy.ops.object.modifier_apply(modifier=modifier.name)
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
