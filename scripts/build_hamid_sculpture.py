"""Khaneh: a white, two-figure carrying study. Run with Blender --background --python.

An interpretive memorial sculpted from the supplied pose reference, not a forensic
reconstruction or an asserted photographic likeness. All export surfaces are white.
"""
import bpy, math, os, random, json
from mathutils import Vector
from math import sin, cos, pi

ROOT = r'C:\Users\Parnia\Documents\Codex\2026-09-17\ok\outputs\khaneh-portraits\assets\sculpture'
os.makedirs(ROOT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
random.seed(14)
sculpture=[]

def material(name, color, roughness=.72):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF'); n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Roughness'].default_value=roughness
    return m
stone=material('Unpigmented white plaster',(0.91,0.91,0.89),.73)

def finish(o,name,mat=stone):
    o.name=name
    if mat: o.data.materials.append(mat)
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=True
    sculpture.append(o); return o

def ellipsoid(name,center,scale,rot=None,seg=40,rings=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=center)
    o=bpy.context.object; o.scale=scale
    if rot: o.rotation_mode='QUATERNION'; o.rotation_quaternion=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name)

def catmull(values,t):
    i=min(int(t),len(values)-2); u=t-i
    a=values[max(0,i-1)];b=values[i];c=values[i+1];d=values[min(len(values)-1,i+2)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

def sweep(name,coords,widths,depths=None,ref=(0,1,0),steps=48,sides=32,cloth=0):
    pts=[Vector(p) for p in coords]; widths=list(widths); depths=depths or widths
    verts=[]; faces=[]; r=Vector(ref)
    for i in range(steps+1):
        t=(len(pts)-1)*i/steps
        c=catmull(pts,t); tangent=(catmull(pts,min(len(pts)-1,t+.01))-catmull(pts,max(0,t-.01))).normalized()
        a=(r-tangent*r.dot(tangent)).normalized()
        if a.length<.1: a=tangent.cross(Vector((1,0,0))).normalized()
        b=tangent.cross(a).normalized()
        w=catmull(widths,t); d=catmull(depths,t)
        for j in range(sides):
            q=2*pi*j/sides
            ripple=1+cloth*(.55*sin(i*.93+q*2)+.25*sin(i*1.7-q*3)+.2*sin(q*7+i*.31))*sin(pi*i/steps)**.5
            verts.append(c+(a*w*cos(q)+b*d*sin(q))*ripple)
    for i in range(steps):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;c=(i+1)*sides+(j+1)%sides;d=(i+1)*sides+j
            faces.append((a,b,c,d))
    verts.extend((pts[0],pts[-1])); first=len(verts)-2;last=first+1
    for j in range(sides):
        faces.append((first,(j+1)%sides,j))
        faces.append((last,steps*sides+j,steps*sides+(j+1)%sides))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    return finish(o,name)

def line(name,coords,radius=.003):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=radius;c.bevel_resolution=2
    s=c.splines.new('BEZIER');s.bezier_points.add(len(coords)-1)
    for p,co in zip(s.bezier_points,coords):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(stone);sculpture.append(o);return o

def union(name,objects,voxel=.012,smooth=4):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join();o=bpy.context.object;o.name=name
    for x in objects[1:]:
        if x in sculpture:sculpture.remove(x)
    mod=o.modifiers.new('Joined sculpted volume','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel;mod.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=o.modifiers.new('Hand smoothed plaster','SMOOTH');mod.factor=.7;mod.iterations=smooth
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in o.data.polygons:p.use_smooth=True
    return o

# Carrier: forward weight, jacket bunched at the waist, separated running legs.
body=sweep('Carrier jacket torso',[(-.06,0,1.02),(-.04,0,1.15),(.07,0,1.37),(.23,0,1.55),(.30,0,1.62)],
           [.165,.175,.205,.215,.08],[.13,.14,.145,.135,.07],cloth=.028)
near_arm=sweep('Carrier near sleeve',[(.20,-.16,1.54),(.17,-.245,1.39),(.18,-.285,1.25),(.36,-.235,1.15),(.46,-.17,1.16)],
               [.10,.11,.10,.082,.073],[.10,.095,.085,.072,.064],cloth=.055)
far_arm=sweep('Carrier far sleeve',[(.28,.165,1.56),(.48,.245,1.41),(.57,.215,1.24),(.50,.12,1.15)],
             [.096,.103,.088,.067],[.097,.094,.082,.062],cloth=.045)
union('Carrier | hooded jacket',[body,near_arm,far_arm],.011,3)
hips=ellipsoid('Carrier trouser hips',(-.065,0,1.02),(.17,.165,.16))
frontleg=sweep('Carrier planted leg',[(.025,-.1,1.02),(.20,-.135,.80),(.32,-.17,.57),(.29,-.18,.34),(.27,-.20,.13)],
               [.115,.125,.104,.082,.071],[.12,.12,.105,.085,.075],cloth=.055)
backleg=sweep('Carrier extended leg',[(-.14,.1,1.03),(-.34,.11,.81),(-.60,.095,.57),(-.80,.08,.35),(-.98,.07,.14)],
              [.115,.12,.095,.079,.067],[.117,.12,.10,.083,.073],cloth=.045)
union('Carrier | trousers',[hips,frontleg,backleg],.010,3)

# Modest cuffs, zipper and the relaxed folds around pockets and elbows.
sweep('Jacket near knitted cuff',[(.402,-.204,1.154),(.462,-.170,1.156)],[.077,.073],[.069,.066],steps=9,cloth=.012)
sweep('Jacket far knitted cuff',[(.525,.156,1.185),(.496,.112,1.144)],[.07,.067],[.065,.06],steps=9)
line('Jacket front zipper',[(.342,-.002,1.555),(.251,-.002,1.44),(.204,-.002,1.32),(.117,-.002,1.16),(.062,-.002,1.02)],.003)
line('Near sleeve elbow fold',[(.125,-.357,1.287),(.205,-.367,1.271),(.259,-.327,1.247)],.006)
line('Near sleeve fold two',[(.11,-.35,1.335),(.175,-.352,1.317),(.224,-.326,1.303)],.004)
line('Near hip pocket opening',[(-.015,-.158,1.09),(.037,-.181,1.035),(.045,-.183,.981)],.004)
line('Planted trouser crease',[(.19,-.247,.805),(.24,-.278,.680),(.329,-.263,.574)],.003)
line('Trouser knee fold',[(.282,-.262,.538),(.33,-.278,.569),(.392,-.232,.584)],.005)
line('Rear trouser fold',[(-.53,-.015,.608),(-.59,-.008,.564),(-.62,.007,.503)],.004)

def sneaker(name,ankle,yaw=0,raised=False):
    ax,ay,az=ankle
    # Hand-built shoe last: broad rounded forefoot, narrow heel, raised instep.
    centers=[(-.085,.0,.065),(-.035,0,.077),(.055,0,.055),(.13,0,.046),(.163,0,.035)]
    coords=[(ax+x,ay+y,z) for x,y,z in centers]
    o=sweep(name+' upper',coords,[.052,.067,.073,.066,.01],[.045,.066,.039,.029,.009],ref=(0,1,0),steps=28,sides=32,cloth=.018)
    # Two uninterrupted sole edges; same unpigmented material as the whole statue.
    sole=[]
    for i in range(33):
        q=i*2*pi/32
        x=ax+.037+.129*cos(q);y=ay+.071*sin(q);z=.02
        sole.append((x,y,z))
    line(name+' sole welt',sole,.014)
    line(name+' fine sole rim',[(x,y,z+.023) for x,y,z in sole],.004)
    for n in range(4):
        x=ax-.015+n*.022;z=.116-n*.009
        line(name+' lace '+str(n),[(x-.012,ay-.046,z-.014),(x+.007,ay,z+.005),(x-.005,ay+.046,z-.014)],.004)
    line(name+' heel seam',[(ax-.08,ay-.048,.050),(ax-.092,ay,.102),(ax-.08,ay+.048,.050)],.003)
sneaker('Carrier forward shoe',(.27,-.2,.1))
sneaker('Carrier trailing shoe',(-.98,.07,.1))

# Second adult: a crosswise, asymmetric load across the carrier's upper back.
# Anatomical sweep runs from drooping shoulders into the pelvis above the far shoulder.
carried_body=sweep('Carried jacket torso',[(-.15,-.26,1.655),(-.04,-.18,1.765),(.15,.01,1.815),(.245,.255,1.805),(.26,.34,1.78)],
                   [.105,.17,.175,.16,.14],[.10,.17,.195,.145,.12],ref=(1,0,0),steps=54,cloth=.023)
carried_neararm=sweep('Carried hanging near sleeve',[(-.11,-.29,1.685),(-.29,-.35,1.50),(-.37,-.36,1.27),(-.28,-.30,1.09)],
                      [.087,.105,.083,.06],[.09,.10,.08,.057],cloth=.05)
carried_fararm=sweep('Carried hanging far sleeve',[(.09,-.31,1.765),(-.07,-.44,1.55),(-.21,-.42,1.28),(-.19,-.30,1.12)],
                     [.087,.095,.078,.06],[.09,.089,.077,.055],cloth=.05)
union('Carried adult | jacket',[carried_body,carried_neararm,carried_fararm],.010,3)
carriedhip=ellipsoid('Carried pelvis',(.235,.285,1.815),(.145,.15,.13))
carriedleg_near=sweep('Carried near bent leg',[(.28,.26,1.81),(.43,.20,1.73),(.53,.095,1.59),(.52,-.035,1.42),(.445,-.105,1.21)],
                      [.105,.114,.092,.082,.062],[.108,.12,.10,.084,.065],cloth=.048)
carriedleg_far=sweep('Carried far bent leg',[(.195,.365,1.83),(.35,.43,1.73),(.48,.355,1.59),(.47,.275,1.44),(.43,.19,1.225)],
                     [.107,.115,.093,.08,.061],[.11,.114,.096,.082,.064],cloth=.045)
union('Carried adult | folded trousers',[carriedhip,carriedleg_near,carriedleg_far],.010,3)
# Feet hang naturally beyond the holding hands, distinct from the carrier's arms.
for label,pos in [('near',(.46,-.11,1.145)),('far',(.45,.19,1.16))]:
    rot=Vector((.7,0,-.7)).to_track_quat('X','Z')
    ellipsoid('Carried '+label+' shoe',pos,(.12,.067,.07),rot)
    x,y,z=pos
    line('Carried '+label+' sole seam',[(x-.06,y-.058,z+.043),(x+.047,y-.061,z-.047),(x+.10,y,z-.067),(x+.047,y+.061,z-.047),(x-.06,y+.058,z+.043)],.004)
line('Carried jacket shoulder fold',[(-.202,-.297,1.665),(-.201,-.365,1.62),(-.177,-.403,1.56)],.004)
line('Carried trouser knee fold',[(.554,-.002,1.61),(.602,.045,1.62),(.58,.114,1.625)],.005)

# White hands: individual slightly bent fingers and opposable thumbs.
def hand(name,wrist,palm,finger_direction,grasp=False):
    wrist=Vector(wrist);palm=Vector(palm);d=Vector(finger_direction).normalized()
    q=(palm-wrist).to_track_quat('Z','Y')
    ellipsoid(name+' palm',palm,(.039,.023,.051),q,32,22)
    cross=Vector((0,1,0))
    if abs(cross.dot(d))>.8:cross=Vector((1,0,0))
    side=d.cross(cross).normalized()
    for i in range(4):
        start=palm+d*.025+side*((i-1.5)*.019)
        length=[.061,.073,.070,.054][i]
        mid=start+d*length*.6
        tip=start+d*length
        if grasp:mid+=cross*.009;tip+=cross*.022-d*.014
        sweep(name+' finger '+str(i+1),[start,mid,tip],[.0105,.01,.0065],steps=12,sides=12)
        line(name+' knuckle '+str(i+1),[mid-side*.006,mid+cross*.009,mid+side*.006],.0015)
    start=palm-side*.033-d*.008
    sweep(name+' thumb',[start,start+d*.025-side*.018,start+d*.047-side*.01],[.016,.013,.009],steps=14,sides=16)
hand('Carrier near supporting hand',(.46,-.17,1.16),(.493,-.13,1.175),(0,.15,.95),True)
hand('Carrier far supporting hand',(.5,.12,1.15),(.465,.09,1.195),(-.1,-.8,.65),True)
hand('Carried near relaxed hand',(-.28,-.30,1.09),(-.249,-.28,1.04),(.2,0,-1))
hand('Carried far relaxed hand',(-.19,-.30,1.12),(-.173,-.27,1.07),(.2,.1,-1))

# Faces are original, simplified sculptural studies rather than claimed likenesses.
def head(name,location,facing,hood=False):
    prior=set(sculpture);loc=Vector(location);q=Vector(facing).normalized().to_track_quat('X','Z')
    parts=[ellipsoid(name+' head',(0,0,0),(.095,.077,.12),seg=48,rings=32)]
    parts.append(ellipsoid(name+' jaw',(.036,0,-.061),(.060,.061,.065)))
    parts.append(ellipsoid(name+' nose bridge',(.085,0,.004),(.020,.014,.040),seg=28,rings=20))
    parts.append(ellipsoid(name+' nose tip',(.1,0,-.014),(.017,.02,.015),seg=24,rings=16))
    for s in [-1,1]:
        parts.append(ellipsoid(name+' cheek '+str(s),(.072,s*.042,-.016),(.021,.024,.031),seg=24,rings=18))
        parts.append(ellipsoid(name+' ear '+str(s),(-.002,s*.075,-.008),(.02,.012,.032),seg=24,rings=18))
    union(name+' sculpted face',parts,.0035,4)
    for s in [-1,1]:
        line(name+' brow '+str(s),[(.078,s*.017,.044),(.078,s*.035,.05),(.060,s*.058,.038)],.0028)
        line(name+' eyelid '+str(s),[(.087,s*.017,.028),(.088,s*.035,.025),(.071,s*.053,.026)],.0018)
    line(name+' upper lip',[(.086,-.023,-.048),(.097,0,-.045),(.086,.023,-.048)],.002)
    line(name+' lower lip',[(.086,-.020,-.051),(.096,0,-.055),(.086,.020,-.051)],.002)
    if not hood:
        # Hair as shallow sculpted locks following the head, all in the same plaster.
        for i in range(14):
            a=-pi*.82+i*pi*1.64/13
            coords=[]
            for j in range(8):
                t=j/7
                x=-.078+.134*t; y=.073*cos(a)*(1-.22*t);z=.037+.088*sin(pi*.15+t*pi*.7)*sin(a*.5+pi*.5)
                coords.append((x,y,z))
            line(name+' hair lock '+str(i),coords,.006)
    for o in set(sculpture)-prior:
        o.location=loc+q@o.location
        o.rotation_mode='QUATERNION';o.rotation_quaternion=q@o.rotation_quaternion
    return q

carrier_headloc=(.416,-.022,1.764)
carrier_facing=(.94,-.15,-.23)
head('Carrier',carrier_headloc,carrier_facing,True)
sweep('Carrier neck',[(.31,0,1.58),(.37,-.01,1.675)],[.069,.068],steps=14)
head('Carried adult',(-.192,-.365,1.564),(-.36,-.46,-.81),False)
sweep('Carried neck',[(-.13,-.29,1.65),(-.181,-.346,1.595)],[.061,.055],steps=12)

# A thick open hood; the face is visible in its opening and not buried in a sphere.
verts=[];faces=[];N=48;M=24;loc=Vector(carrier_headloc);q=Vector(carrier_facing).to_track_quat('X','Z')
for i in range(M+1):
    th=.92+(pi-.92-.01)*i/M
    for j in range(N):
        a=j*2*pi/N
        v=Vector((.125*cos(th),.132*sin(th)*cos(a),.165*sin(th)*sin(a)))
        v.x-=.019
        verts.append(loc+q@v)
for i in range(M):
    for j in range(N):faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
mesh=bpy.data.meshes.new('Soft hood');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('Carrier | open hood',mesh);bpy.context.collection.objects.link(o);finish(o,o.name)
mod=o.modifiers.new('Hood fabric thickness','SOLIDIFY');mod.thickness=.018
bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
rim=[]
for j in range(N+1):
    a=j*2*pi/N;rim.append(loc+q@Vector((.125*cos(.92)-.019,.132*sin(.92)*cos(a),.165*sin(.92)*sin(a))))
line('Hood rolled opening',rim,.008)
line('Hood crown seam',[loc+q@Vector((-.132,0,-.02)),loc+q@Vector((-.09,0,.13)),loc+q@Vector((.03,0,.157)),loc+q@Vector((.077,0,.106))],.004)
sweep('Raised jacket collar',[(.27,-.09,1.578),(.35,-.095,1.628),(.43,-.06,1.641)],[.036,.041,.027],steps=20)

# Plinth: no lettering, colors, or scenery, only the quiet weight of the sculpture.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1,depth=.08,location=(-.15,0,-.04))
plinth=bpy.context.object;plinth.scale=(1.08,.63,1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
finish(plinth,'Oval white memorial plinth')
bevel=plinth.modifiers.new('Rounded plinth edge','BEVEL');bevel.width=.018;bevel.segments=3
bpy.context.view_layer.objects.active=plinth;bpy.ops.object.modifier_apply(modifier=bevel.name)

# Bake curve surfaces for a self-contained viewer asset.
for o in list(sculpture):
    if o.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.convert(target='MESH')

# Smooth subtle high-frequency surfaces and decimate only oversized components.
for o in sculpture:
    if o.type=='MESH' and len(o.data.polygons)>12000:
        bpy.context.view_layer.objects.active=o
        m=o.modifiers.new('Browser mesh optimization','DECIMATE');m.ratio=12000/len(o.data.polygons)
        bpy.ops.object.modifier_apply(modifier=m.name)

# Asset coordinate system in GLB is +Y up; glTF exporter performs that conversion.
bpy.ops.object.select_all(action='DESELECT')
for o in sculpture:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'hamid-carrying-white.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT')
corners=[o.matrix_world@Vector(c) for o in sculpture for c in o.bound_box]
blmin=[min(v[i] for v in corners) for i in range(3)]
blmax=[max(v[i] for v in corners) for i in range(3)]
with open(os.path.join(ROOT,'sculpture-metadata.json'),'w',encoding='utf-8') as f:
    json.dump({'title':'Hamid Mahdavi — a carrying study','kind':'Original interpretive white memorial maquette',
               'note':'Pose study from a supplied reference; facial features are sculptural interpretations, not a verified likeness.',
               'coordinates':'glTF +Y up, meters','bounds':{'min':[blmin[0],blmin[2],-blmax[1]],'max':[blmax[0],blmax[2],-blmin[1]]},
               'cameraPosition':[2.5,2.9,8.5],'cameraTarget':[-.1,1.04,0],
               'recommendedOrbit':'17deg 78deg 112%','polygons':sum(len(o.data.polygons) for o in sculpture if o.type=='MESH'),
               'triangles':sum(len(p.vertices)-2 for o in sculpture if o.type=='MESH' for p in o.data.polygons),
               'materials':'One unpigmented white plaster material; no textures or color maps',
               'compression':'Uncompressed GLB; no decoder or external asset dependencies'},f,indent=2)

# Studio presentation camera: same right-facing silhouette as reference, slightly above.
scene=bpy.context.scene
for eng in ['BLENDER_EEVEE_NEXT','BLENDER_EEVEE']:
    try:scene.render.engine=eng;break
    except:pass
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.render.filepath=os.path.join(ROOT,'hamid-carrying-white.png')
scene.world.color=(.25,.25,.25)
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.6,.6,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
def area(name,loc,power,size,target=(0,0,1)):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large soft window',(-3,-4,5),600,4)
area('White fill',(4,-1,3),320,3)
area('Contour light',(1,3,4),800,3)
bpy.ops.object.camera_add(location=(2.5,-8.5,2.9))
cam=bpy.context.object;cam.name='Memorial study camera';target=Vector((-.10,0,1.04));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.82;scene.camera=cam
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.image_settings.color_mode='RGBA'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'hamid-carrying-white.blend'))
bpy.ops.render.render(write_still=True)
print('SCULPTURE_COMPLETE',sum(len(o.data.polygons) for o in sculpture if o.type=='MESH'),'polygons')
print('GLTF_CAMERA',[2.5,2.9,8.5],'TARGET',[-.10,1.04,0])
