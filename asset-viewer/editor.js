import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';
import {Sky} from 'three/addons/objects/Sky.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
const $ = id => document.getElementById(id);
const scene = new T.Scene(), camera = new T.PerspectiveCamera(45,1,.1,5000);
const renderer = new T.WebGLRenderer({antialias:true});
renderer.shadowMap.enabled = true;
renderer.toneMapping = T.ACESFilmicToneMapping;      // Cities: Skylines II (Unity HDRP) look: filmic tonemap
document.body.append(renderer.domElement);
camera.position.set(30,25,35);
const orbit = new OrbitControls(camera,renderer.domElement);
orbit.addEventListener('change', () => {
 camera.near = Math.max(0.1, camera.position.distanceTo(orbit.target) / 100);
 camera.updateProjectionMatrix();
});
// --- Lighting tuned towards Cities: Skylines II (HDRP): physical sky, warm low sun, blue moonlit night,
// distance haze, sky reflections, bloom on emissive lights. An approximation, not the game renderer.
const sky = new T.HemisphereLight(0xcde4ff,0x645347,1);
const sun = new T.DirectionalLight(0xffe5bd,3);
const moon = new T.DirectionalLight(0x9db4ff,0);
moon.position.set(140,220,160);
sun.castShadow = true;
sun.shadow.bias = -0.00015;
sun.shadow.normalBias = 0.12;
$('shadows').onchange = () => { sun.castShadow = $('shadows').checked; };
Object.assign(sun.shadow.camera,{left:-180,right:180,top:180,bottom:-180,far:900});
sun.shadow.mapSize.set(4096,4096);
const ground = new T.Mesh(new T.PlaneGeometry(4000,4000),new T.MeshStandardMaterial({color:0x4d5a47,roughness:1}));
ground.rotation.x = -Math.PI/2;
ground.receiveShadow = true;
const grid = new T.GridHelper(400,80,0x8a9488,0x6b7568);
grid.position.y = 0.025;
grid.material.transparent = true;
grid.material.opacity = .35;
const skyDome = new Sky();
skyDome.scale.setScalar(4500);
skyDome.material.uniforms.turbidity.value = 8;
skyDome.material.uniforms.rayleigh.value = 2.6;
skyDome.material.uniforms.mieCoefficient.value = .004;
skyDome.material.uniforms.mieDirectionalG.value = .8;
scene.fog = new T.FogExp2(0x9ec7e8,.00022);
scene.add(sky,sun,moon,ground,grid,skyDome);
const pmrem = new T.PMREMGenerator(renderer);
const envScene = new T.Scene();
const envSky = new Sky();
envSky.scale.setScalar(4500);
envSky.material.uniforms.turbidity.value = 8;
envSky.material.uniforms.rayleigh.value = 2.6;
envSky.material.uniforms.mieCoefficient.value = .004;
envSky.material.uniforms.mieDirectionalG.value = .8;
envScene.add(envSky);
let envTarget = null, envTime = -99;
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
const bloom = new UnrealBloomPass(new T.Vector2(1,1),.3,.4,1.15);
composer.addPass(bloom);
composer.addPass(new OutputPass());
const emissiveMaterials = new Set();
const smooth = (a,b,x)=>{ const t=Math.min(1,Math.max(0,(x-a)/(b-a))); return t*t*(3-2*t); };
function lighting(){
 const t=+$('time').value, a=(t-6)*Math.PI/12;
 const elevation=Math.asin(Math.sin(a)*.84);                 // noon sun ~57 deg high (mid latitude)
 const day=smooth(-.07,.14,elevation), low=1-smooth(.05,.45,elevation), night=1-smooth(-.16,.02,elevation);
 const dir=new T.Vector3(Math.cos(a)*Math.cos(elevation),Math.sin(elevation),.45*Math.cos(elevation)).normalize();
 sun.position.copy(dir).multiplyScalar(400);
 sun.color.set(0xfff4e2).lerp(new T.Color(0xff9a4a),low);    // white noon sun, orange near the horizon
 sun.intensity=2.5*smooth(-.02,.22,elevation);
 moon.intensity=1.3*night;
 sky.color.set(0x31457c).lerp(new T.Color(0xbdd8ff),day);
 sky.groundColor.set(0x141a2a).lerp(new T.Color(0x6b6052),day);
 sky.intensity=1.7-1.15*day;
 for(const u of [skyDome.material.uniforms,envSky.material.uniforms])u.sunPosition.value.copy(dir);
 skyDome.visible=day>.02;
 const horizon=new T.Color(0x0b1326).lerp(new T.Color(0xf0b98a),Math.min(day*3,1)*low).lerp(new T.Color(0xa9cdea),day*(1-low));
 scene.background=day>.02?null:horizon;
 scene.fog.color.copy(horizon);
 scene.fog.density=.00018+.00018*low;
 renderer.toneMappingExposure=.4+.75*night+.1*low*day;       // eye adaptation: brighter exposure at night
 if(Math.abs(t-envTime)>.2){                                  // sky reflections (glass, metal)
  envTime=t;
  envTarget?.dispose();
  envTarget=pmrem.fromScene(envScene,0,.1,5000);
  scene.environment=envTarget.texture;
 }
 scene.environmentIntensity=.15+.4*day;
 const lit=1-smooth(-.02,.16,elevation);                      // building lights come on around dusk
 for(const material of emissiveMaterials)material.emissiveIntensity=2.2*lit;
 bloom.enabled=lit>.02;                                       // sky and sunlit walls must not bloom
 bloom.strength=.32*lit;
 $('hour').value=t.toFixed(1)+'시';
}
$('time').oninput=lighting;
lighting();
const models=new Map();
const selected=()=>models.get($('assets').value);
$('assets').onchange=()=>{
 const m=selected();
 $('x').value=m?.position.x??0;
 $('z').value=m?.position.z??0;
 $('angle').value=m?T.MathUtils.radToDeg(m.rotation.y):0;
};
for(const id of ['x','z','angle']) $(id).oninput=()=>{
 const m=selected();
 if(!m)return;
 m.position.x=+$('x').value;
 m.position.z=+$('z').value;
 m.rotation.y=T.MathUtils.degToRad(+$('angle').value);
};
$('remove').onclick=()=>{
 const m=selected();
 if(!m)return;
 scene.remove(m);
 m.traverse(o=>emissiveMaterials.delete(o.material));
 models.delete(m.uuid);
 $('assets').selectedOptions[0].remove();
 $('assets').onchange();
};
async function loadAsset(file, files){
 const data=await file.arrayBuffer();
 if(!/\.fbx$/i.test(file.name))return (await new GLTFLoader().parseAsync(data,'')).scene;
 const stem=file.name.slice(0,-4);
 const manager=new T.LoadingManager();
 const textureUrls=new Map();
 manager.setURLModifier(url=>{
  if(/^(blob:|data:)/i.test(url))return url;
  const name=url.split(/[\\/]/).pop().toLowerCase();
  const image=files.get(name);
  if(!image)return url;
  if(!textureUrls.has(name))textureUrls.set(name,URL.createObjectURL(image));
  return textureUrls.get(name);
 });
 manager.onLoad=()=>{
  for(const url of textureUrls.values())URL.revokeObjectURL(url);
  textureUrls.clear();
 };
 const loader=new FBXLoader(manager);
 const model=new T.Group();
 const atlasParts=[];
 for(const part of [file,files.get((stem+'_Win.fbx').toLowerCase()),files.get((stem+'_Gls.fbx').toLowerCase())].filter(Boolean)){
  const mesh=loader.parse(part===file?data:await part.arrayBuffer(),'');
  mesh.scale.multiplyScalar((mesh.userData.unitScaleFactor??1)/100);
  model.add(mesh);
  if(part===file || /_win\.fbx$/i.test(part.name))atlasParts.push(mesh);
 }
 const colorFile=files.get((stem+'_BaseColor.png').toLowerCase());
 if(colorFile){
  const url=URL.createObjectURL(colorFile);
  try{
   const map=await new T.TextureLoader().loadAsync(url);
   map.colorSpace=T.SRGBColorSpace;
   const material=new T.MeshStandardMaterial({map});
   const mask=files.get((stem+'_MaskMap.png').toLowerCase());
   if(mask){
    const bitmap=await createImageBitmap(mask,{premultiplyAlpha:'none',colorSpaceConversion:'none'});
    const canvas=new OffscreenCanvas(bitmap.width,bitmap.height), g=canvas.getContext('2d',{willReadFrequently:true});
    g.drawImage(bitmap,0,0);
    const image=g.getImageData(0,0,bitmap.width,bitmap.height), d=image.data;
    for(let i=0;i<d.length;i+=4){ const metal=d[i], gloss=d[i+3]; d[i]=255; d[i+1]=255-gloss; d[i+2]=metal; d[i+3]=255; }
    g.putImageData(image,0,0);
    const texture=new T.CanvasTexture(canvas);
    material.roughnessMap=material.metalnessMap=texture;      // three: G = roughness, B = metalness
    material.roughness=1; material.metalness=1;
   }
   const normal=files.get((stem+'_Normal.png').toLowerCase());
   if(normal){
    const normalUrl=URL.createObjectURL(normal);
    try{material.normalMap=await new T.TextureLoader().loadAsync(normalUrl);}
    finally{URL.revokeObjectURL(normalUrl);}
   }
   const emission=files.get((stem+'_Emissive.png').toLowerCase());
   if(emission){
    const emissionUrl=URL.createObjectURL(emission);
    try{
     material.emissiveMap=await new T.TextureLoader().loadAsync(emissionUrl);
     material.emissiveMap.colorSpace=T.SRGBColorSpace;
     material.emissive.set(0xffffff);
     emissiveMaterials.add(material);
     lighting();
    }finally{URL.revokeObjectURL(emissionUrl);}
   }
   for(const part of atlasParts)part.traverse(o=>{
    if(o.isMesh && o.geometry.attributes.uv)o.material=material;
   });
  }finally{URL.revokeObjectURL(url);}
 }
 return model;
}
async function importFiles(selection){
 const folders=new Map();
 for(const file of selection){
  const path=file.webkitRelativePath || file.name;
  const folder=path.slice(0,path.lastIndexOf('/')+1);
  if(!folders.has(folder))folders.set(folder,new Map());
  folders.get(folder).set(file.name.toLowerCase(),file);
 }
 const errors=[];
 let imported=0;
 for(const files of folders.values()){
 const sources=[...files.values()].filter(f=>/\.(glb|fbx)$/i.test(f.name) &&
  !(/_(win|gls)\.fbx$/i.test(f.name) && files.has(f.name.replace(/_(win|gls)\.fbx$/i,'.fbx').toLowerCase())) &&
  !(/_lod[12](?:_(?:win|gls))?\.fbx$/i.test(f.name) && files.has(f.name.replace(/_lod[12](?:_(?:win|gls))?\.fbx$/i,'.fbx').toLowerCase())));
 for(const f of sources){
 try{
  const model=await loadAsset(f,files);
  const bounds=new T.Box3().setFromObject(model);
  if(bounds.isEmpty())throw Error('표시할 메시가 없습니다.');
  const center=bounds.getCenter(new T.Vector3());
  model.position.sub(new T.Vector3(center.x,bounds.min.y,center.z));
  model.traverse(o=>{if(o.isMesh)o.castShadow=o.receiveShadow=true;});
  const placed=new T.Group();
  placed.add(model);
  if(models.size){
   const right=Math.max(...Array.from(models.values(),asset=>new T.Box3().setFromObject(asset).max.x));
   placed.position.x=right+(bounds.max.x-bounds.min.x)/2+5;
  }
  models.set(placed.uuid,placed);
  scene.add(placed);
  $('assets').add(new Option(f.name,placed.uuid,true,true));
  $('assets').value=placed.uuid;
  $('assets').onchange();
  const size=Math.max(2,bounds.getSize(new T.Vector3()).length());
  orbit.target.set(placed.position.x,(bounds.max.y-bounds.min.y)/2,placed.position.z);
  camera.position.copy(orbit.target).add(new T.Vector3(.8,.5,1).multiplyScalar(size));
  camera.far=Math.max(5000,size*5);
  camera.updateProjectionMatrix();
  orbit.update();
  imported++;
 }catch(error){errors.push(f.name+': '+error.message);}
 }
 }
 $('status').value=(imported ? imported+' \uac1c \uac00\uc838\uc634' : '')+(errors.length?' '+errors.join(' / '): imported?'':'GLB / FBX files not found.');
}
for(const id of ['file','folder'])$(id).onchange=()=>{
 const input=$(id);
 const files=Array.from(input.files);
 input.value='';
 if(files.length)return importFiles(files);
};
function resize(){
 const height=Math.max(1,innerHeight-document.querySelector('header').offsetHeight);
 renderer.setSize(innerWidth,height);
 composer.setSize(innerWidth,height);
 camera.aspect=innerWidth/height;
 camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(document.querySelector('header'));
window.addEventListener('resize',resize);
resize();
renderer.setAnimationLoop(()=>composer.render());

const preview = new URLSearchParams(location.search).get('preview');
if(preview === '103'){
 const stem='HighriseTower103_L1_5x4';
 const transfer=new DataTransfer();
 try{
  for(const suffix of ['.fbx','_Win.fbx','_BaseColor.png','_Normal.png','_MaskMap.png','_Emissive.png']){
   const name=stem+suffix;
   const response=await fetch('/preview/'+name);
   if(!response.ok)throw Error(name);
   transfer.items.add(new File([await response.blob()],name));
  }
  $('file').files=transfer.files;
  await $('file').onchange();
 }catch(error){$('status').value=error.message;}
}
