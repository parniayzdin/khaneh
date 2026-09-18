"""Interpretive standing peace-sign study. No facial detail."""
import bpy, math
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parents[1]/'outputs/khaneh-portraits/assets/sculpture'
bpy.ops.wm.read_factory_settings(use_empty=True)
mat=bpy.data.materials.new('White plaster');mat.diffuse_color=(.9,.9,.88,1)
def finish(obj,name):
    obj.name='Nika / '+name;obj.data.materials.append(mat)
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

# Relaxed standing stance, loose top and trousers; no facial features.
limb('left trouser',(-.10,0,.86),(-.16,-.025,.18),.105,.115)
limb('right trouser',(.10,.03,.86),(.19,.025,.18),.105,.115)
oval('left shoe',(-.16,-.065,.085),(.085,.155,.075))
oval('right shoe',(.19,-.045,.085),(.085,.155,.075))
oval('shirt hem',(0,0,.88),(.205,.13,.17))
limb('loose shirt torso',(0,0,.91),(-.025,0,1.31),.20,.13)
limb('neck',(-.025,0,1.38),(-.025,0,1.48),.065)
head=oval('head',(-.025,-.01,1.59),(.115,.10,.15));head.rotation_euler.y=-.1
oval('short hair',(-.025,.025,1.66),(.12,.095,.10))
# Left arm rises beside the head. Two separated straight fingers form the V.
limb('raised upper sleeve',(-.18,0,1.32),(-.32,-.015,1.14),.087)
limb('raised forearm',(-.32,-.015,1.14),(-.46,-.06,1.53),.056)
oval('peace hand palm',(-.46,-.06,1.61),(.063,.033,.085))
limb('peace index',(-.489,-.06,1.67),(-.56,-.06,1.86),.020)
limb('peace middle',(-.436,-.06,1.67),(-.39,-.06,1.87),.020)
oval('folded fingers',(-.43,-.09,1.605),(.037,.025,.044))
limb('thumb',(-.50,-.09,1.59),(-.445,-.104,1.63),.022)
limb('resting upper sleeve',(.17,0,1.31),(.26,-.01,1.05),.077)
limb('resting forearm',(.26,-.01,1.05),(.25,-.06,.86),.054)
oval('resting hand',(.25,-.06,.80),(.049,.035,.077))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(root/'nika-peace-white.glb'),export_format='GLB',use_selection=True,export_yup=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'nika-peace-white.blend'))
print('NIKA_SCULPTURE_SAVED')
