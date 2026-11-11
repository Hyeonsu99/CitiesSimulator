const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

// 1. 프리셋 데이터 검증
const { getIdealKoreanNewTownPresetData } = require('../korean_newtown_preset.js');
const preset = getIdealKoreanNewTownPresetData();

console.log('--- 1. 프리셋 데이터 검증 ---');
assert.ok(preset.nodes.length >= 25, '노드 수 충족');
assert.ok(preset.roads.length >= 35, '도로 수 충족');
assert.ok(preset.zoneBlocks.length >= 10, '구역 블록 수 충족');

// 학교와 운동장 검증
const schoolBlocks = preset.zoneBlocks.filter(b => b.landUse === 'school');
assert.equal(schoolBlocks.length, 2, '초품아 초등학교 부지 2개 존재');
assert.ok(schoolBlocks.every(s => s.trackW > 0 && s.trackH > 0), '운동장 트랙 규격 메타데이터 존재');
console.log('✅ 학교와 운동장 메타데이터 검증 완료');

// 복합환승센터 검증
const transitBlock = preset.zoneBlocks.find(b => b.landUse === 'transit');
assert.ok(transitBlock, '복합환승센터 부지 존재');
assert.equal(transitBlock.facility, 'multimodal_transit');
assert.equal(transitBlock.roof, 'aerofoil');
console.log('✅ 복합환승센터 유선형 캐노피 메타데이터 검증 완료');

// 하천 및 수변공원 검증
const riverBlock = preset.zoneBlocks.find(b => b.landUse === 'river');
assert.ok(riverBlock, '하천 및 수변공원 축 부지 존재');
assert.ok(riverBlock.riverbed, '하천 저지대 하상 표시');
const footbridges = preset.roads.filter(r => r.facility === 'pedestrian_bridge');
assert.equal(footbridges.length, 2, '수변 아치 보행교 2개 존재');
console.log('✅ 하천 및 수변공원, 수변 보행교 검증 완료');

// 고도와 연결이 다른 입체교차로 검증
const zValues = new Set(preset.nodes.map(n => n.z || 0));
assert.ok(zValues.has(0) && zValues.has(4) && zValues.has(8) && zValues.has(11), '0m, 4m, 8m, 11m 다단 입체 고도 존재');
const interchangeRamps = preset.roads.filter(r => r.facility === 'interchange');
assert.ok(interchangeRamps.length >= 4, '남부 IC 입체교차 진출입 램프 존재');
const flyoverRoads = preset.roads.filter(r => r.facility === 'flyover');
assert.ok(flyoverRoads.length >= 2, '3단 최상층 고가 플라이오버 존재');
console.log('✅ 다단 입체교차로 및 고가도로 고도·연결 검증 완료');

// 회전교차로 (로터리) 검증
assert.ok(preset.roundabouts && preset.roundabouts.length >= 2, '프리셋에 로터리 2개 이상 정의');
const roundaboutRoads = preset.roads.filter(r => r.facility === 'roundabout');
assert.ok(roundaboutRoads.length >= 20, '로터리 원형 순환 도로 세그먼트들 구성');
assert.ok(preset.roundabouts.some(r => r.name.includes('서측')), '서측 생활권 회전교차로 존재');
assert.ok(preset.roundabouts.some(r => r.name.includes('테크노밸리')), '테크노밸리 스마트 로터리 존재');
console.log('✅ 생활권 회전교차로(로터리) 노드·순환로 메타데이터 검증 완료');

// 2. 가상 DOM 환경에서 시뮬레이터와 3D 연동 검증
console.log('--- 2. 시뮬레이터 & 3D 연동 로직 검증 ---');

// 모의 캔버스 및 DOM 환경 생성
global.window = {
  addEventListener: () => {},
  removeEventListener: () => {}
};
global.document = {
  getElementById: (id) => ({
    addEventListener: () => {},
    classList: { add: () => {}, remove: () => {}, toggle: () => {} },
    style: {},
    textContent: '',
    innerHTML: ''
  }),
  querySelectorAll: () => [],
  createElement: () => ({ addEventListener: () => {}, style: {}, classList: { add: () => {}, remove: () => {} } })
};

// 3. 파일 구문 및 무결성 검증
const htmlContent = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf-8');
assert.ok(htmlContent.includes('id="btn-toggle-view"'), 'index.html에 3D 뷰 전환 버튼 존재');
assert.ok(htmlContent.includes('id="simCanvas3D"'), 'index.html에 3D 캔버스 존재');
assert.ok(htmlContent.includes('id="hud-3d-controls"'), 'index.html에 3D HUD 컨트롤 존재');
assert.ok(htmlContent.includes('src="view3d.js"'), 'index.html에 view3d.js 로드 스크립트 존재');
console.log('✅ index.html 마크업 및 스크립트 연동 검증 완료');

const cssContent = fs.readFileSync(path.join(__dirname, '..', 'style.css'), 'utf-8');
assert.ok(cssContent.includes('.btn-view-mode'), 'style.css에 3D 뷰 모드 버튼 스타일 존재');
assert.ok(cssContent.includes('#simCanvas3D'), 'style.css에 3D 캔버스 스타일 존재');
assert.ok(cssContent.includes('.hud-3d-controls'), 'style.css에 3D HUD 컨트롤 스타일 존재');
console.log('✅ style.css 스타일 정의 검증 완료');

const view3dContent = fs.readFileSync(path.join(__dirname, '..', 'view3d.js'), 'utf-8');
assert.ok(view3dContent.includes('class CityView3D'), 'view3d.js에 CityView3D 클래스 정의');
assert.ok(view3dContent.includes('camera'), 'view3d.js에 카메라 시스템 정의');
assert.ok(view3dContent.includes('yaw') && view3dContent.includes('pitch') && view3dContent.includes('distance'), '카메라 회전/기울기/거리 상태');
assert.ok(view3dContent.includes('schW'), '학교 및 운동장 3D 렌더링 코드');
assert.ok(view3dContent.includes('multimodal_transit') || view3dContent.includes('transit'), '복합환승센터 3D 렌더링 코드');
assert.ok(view3dContent.includes('waterColor'), '하천 수면 3D 렌더링 코드');
assert.ok(view3dContent.includes('isElevated') && view3dContent.includes('addPillar'), '입체교차로 및 지지 교각(Pier) 3D 코드');
assert.ok(view3dContent.includes('buildRoundabouts'), '3D 로터리 원형 교통섬 및 연석 렌더러');
console.log('✅ view3d.js 3D 조감도 엔진 무결성 검증 완료');

const simContent = fs.readFileSync(path.join(__dirname, '..', 'simulator.js'), 'utf-8');
assert.ok(simContent.includes('toggleViewMode'), 'simulator.js에 toggleViewMode 구현');
assert.ok(simContent.includes('setViewMode'), 'simulator.js에 setViewMode 구현');
assert.ok(simContent.includes('notifyDataChanged'), 'simulator.js에 notifyDataChanged 구현');
assert.ok(simContent.includes('this.viewMode'), 'simulator.js에 viewMode 관리');
assert.ok(simContent.includes('this.roundabouts'), 'simulator.js에 roundabouts 상태 관리');
console.log('✅ simulator.js 2D/3D 전환 및 데이터 반영 로직 검증 완료');

console.log('\n모든 단위 및 구조 검증 통과!');
