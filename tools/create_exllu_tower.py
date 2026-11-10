import bpy, math, os, random
random.seed(42)
from mathutils import Vector
root=os.path.abspath('assets/exllu')
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def material(name, color, metal=0, rough=.7):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 return m
mats=[material('Ivory precast concrete',(.69,.68,.63)),material('Light concrete trim',(.84,.82,.76)),material('Gray wall panels',(.44,.47,.45)),material('Blue green glazing',(.19,.34,.34),.3,.24),material('Window frames',(.75,.77,.72),.15,.38),material('Balcony glass',(.35,.52,.49),.18,.29),material('Roof glass',(.18,.43,.39),.25,.25),material('Dark stone',(.18,.19,.18)),material('Window pale reflection',(.32,.47,.45),.25,.28),material('Window shaded',(.12,.23,.24),.25,.32),material('Warm concrete accent',(.60,.55,.49)),material('Deep frame shadow',(.27,.30,.29)),material('Balcony rail metal',(.68,.71,.68),.4,.35)]
# Group repeated details by material into a small number of meshes.
vertices=[[] for _ in mats]; faces=[[] for _ in mats]
def box(x,y,z,w,d,h,mi):
 v=vertices[mi]; f=faces[mi]; a=len(v)
 v.extend([(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
 f.extend([tuple(a+i for i in q) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
# Massing: recessed central glazing and two projecting residential wings.
box(0,0,74,30,20,148,0); box(-11,-1.8,74,10,21.6,148,1); box(11,-1.8,74,10,21.6,148,1)
box(0,-10.1,74,10,.16,144,3)
box(0,0,2.2,35,24,4.4,7); box(0,-12.1,2.3,8,.25,3.8,3)
box(0,-12.7,4.3,11,2,.25,1)
for x in (-4,-2,0,2,4): box(x,-12.27,2.0,.08,.1,3.4,4)
for x in (-15,-6,6,15): box(x,-12.35,2.1,.65,.8,4.1,10)
# Recessed window pairs, horizontal slab edges, and balcony rail details.
for floor in range(1,50):
 z=floor*2.94+1.25
 for x in (-13.4,-10.5,-7.6,7.6,10.5,13.4):
  box(x,-12.64,z,2.42,.09,1.92,random.choice((3,3,3,8,9)))
  box(x,-12.71,z,0.07,.07,1.92,4)
  for dx in (-1.25,1.25): box(x+dx,-12.71,z,.08,.10,2.02,4)
  for dz in (-.98,.98): box(x,-12.71,z+dz,2.58,.1,.08,4)
  box(x,-12.72,z-.12,2.42,.07,.07,4)
 for x in (-4,-2,0,2,4):
  box(x,-10.22,z,.065,.08,2.65,4)
 box(0,-10.22,z-1.21,10,.08,.075,4)
 for side in (-1,1):
  for y in (-7.8,-4.4,-1,2.4,5.8):
   box(side*16.07,y,z,.08,2.55,1.85,random.choice((3,3,8,9)))
   box(side*16.13,y,z,.08,.065,1.85,4)
   box(side*16.13,y,z-.12,.08,2.55,.065,4)
  box(side*16.12,-1,z-1.17,.18,19.3,.13,1)
  for y in (-9.9,-6.1,-2.7,.7,4.1,7.5): box(side*16.12,y,z,.13,.12,2.8,1)
  # Projecting balconies on the outer portions of both wings.
  box(side*11,-12.95,z-.93,9.9,.8,.18,1)
  box(side*11,-13.32,z-.37,9.5,.07,.92,5)
  box(side*11,-13.37,z+.10,9.55,.08,.08,12)
  for dx in (-4.5,-3,-1.5,0,1.5,3,4.5): box(side*11+dx,-13.39,z-.38,.055,.08,.95,12)
  for dx in (-4.85,4.85): box(side*11+dx,-13.02,z-.35,.15,.8,1.22,1)
 for x in (-13.5,-10.5,-7.5,7.5,10.5,13.5): box(x,10.04,z,2.4,.08,1.9,3)
 # Pale spandrel bands emphasize individual floors.
 box(0,10.1,z-1.18,31.8,.08,.12,1)
# Vertical strips and crown / sloping glazed roof.
for x in (-16,-6,6,16): box(x,-12.7,75,.5,.65,147,1)
for x in (-5.5,5.5): box(x,-10.32,76,.55,.7,143,10)
for x in (-15.7,15.7): box(x,-12.9,75,.18,.18,145,10)
box(0,0,148.5,32.3,21,1.1,1)
for x in (-15.3,15.3): box(x,-12.4,149.9,1.4,1.1,3.0,1)
for x in (-5.3,5.3): box(x,-10.4,149.5,.55,1,2.5,1)
# Roof glass rises from the facade: low sloping top, approximated from photos.
v=[(-5,-9,149),(5,-9,149),(5,4,149),(-5,4,149),(-5,-9,158),(5,-9,158),(5,4,155),(-5,4,155)]
me=bpy.data.meshes.new('Crown glass'); me.from_pydata(v,[],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]); me.update(); ob=bpy.data.objects.new('Sloped green glass crown',me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mats[6])
for x in range(-5,6,1): box(x,-9.04,153.5,.045,.06,9,4)
for z in (150,151.5,153,154.5,156,157.5): box(0,-9.06,z,10,.06,.045,4)
for y in (-8,-6,-4,-2,0,2):
 for side in (-1,1): box(side*5.03,y,152,.06,.06,6,4)
for side in (-1,1):
 for z in (150,151.5,153,154.5): box(side*5.04,-2.5,z,.06,13,.045,4)
box(10,2,149.6,5,5,1.1,2)
for x in (8.5,10,11.5): box(x,2,150.25,1,3,.2,7)
for i,m in enumerate(mats):
 if not vertices[i]: continue
 me=bpy.data.meshes.new(m.name); me.from_pydata(vertices[i],[],faces[i]); me.update(); obj=bpy.data.objects.new(m.name,me); bpy.context.collection.objects.link(obj); obj.data.materials.append(m)
# Building name belongs to the rooftop, as seen in the reference photograph.
curve=bpy.data.curves.new('EXLLU signage','FONT'); curve.body='EXLLU'; curve.align_x='CENTER'; curve.size=1.7; curve.extrude=.025
sign=bpy.data.objects.new('EXLLU rooftop sign',curve); bpy.context.collection.objects.link(sign); sign.location=(0,-9.14,154); sign.rotation_euler=(math.pi/2,0,0); sign.data.materials.append(mats[1])
bpy.context.view_layer.objects.active=sign; sign.select_set(True); bpy.ops.object.convert(target='MESH'); sign.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'geumgang_exllu_tower.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'geumgang_exllu_tower.glb'),export_format='GLB')
# Preview is not part of the exported model.
bpy.ops.object.light_add(type='SUN'); bpy.context.object.rotation_euler=(.4,-.5,-.5); bpy.context.object.data.energy=2.7
bpy.context.scene.world.use_nodes=True; bpy.context.scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.65,.7,.75,1); bpy.context.scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8
bpy.ops.object.camera_add(location=(115,-195,112)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,80))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=172
s=bpy.context.scene; s.camera=cam; s.render.engine='CYCLES'; s.cycles.samples=32; s.render.resolution_x=1100; s.render.resolution_y=1100; s.render.resolution_percentage=100; s.render.filepath=os.path.join(root,'preview.png'); bpy.ops.render.render(write_still=True)
cam.location=(70,-115,142); cam.rotation_euler=(Vector((0,0,126))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=64
s.render.filepath=os.path.join(root,'detail.png'); bpy.ops.render.render(write_still=True)

