// =======================================================================
// 3D 에셋 품질 고도화 종합 자동 검증 테스트 (test_3d_asset_quality.js)
// 주거·상업·연구 건축물, 가로수·수변·도로 시설, 야외 공간 및 발자국 무결성 검증
// =======================================================================

const assert = require('node:assert/strict');
const { getIdealKoreanNewTownPresetData } = require('../korean_newtown_preset.js');
const { CityView3D, FootprintManager, MeshData } = require('../view3d.js');

console.log('=== [1] 가로수(Tree) 다층 수형 및 수종별 지오메트리 고도화 검증 ===');
const treeMesh = new MeshData();
const treeTypes = ['pine', 'cherry', 'willow', 'ginkgo', 'deciduous', 'shrub'];
for (let i = 0; i < treeTypes.length; i++) {
  const type = treeTypes[i];
  const prevIdx = treeMesh.indices.length;
  treeMesh.addTree(i * 30, 0, 0, 12, 5, type);
  const diffIdx = treeMesh.indices.length - prevIdx;
  assert.ok(diffIdx > 0, `${type} 나무 지오메트리 생성 성공 (인덱스: ${diffIdx})`);
}
console.log(`✅ 6종 수종(적송, 벚나무, 수양버들, 은행나무, 느티나무, 정원관목) 생성 완료 (총 인덱스: ${treeMesh.indices.length})`);

console.log('\n=== [2] 신도시 조감도 전체 지오메트리 빌드 및 에셋 품질 검증 ===');
const preset = getIdealKoreanNewTownPresetData();

const zoneCells = new Map();
const cellSize = 16;
for (const b of preset.zoneBlocks) {
  for (let x = b.x; x < b.x + b.w; x += cellSize) {
    for (let y = b.y; y < b.y + b.h; y += cellSize) {
      zoneCells.set(`${x},${y}`, { x, y, type: b.type, landUse: b.landUse, name: b.name });
    }
  }
}

const mockSim = {
  roads: preset.roads,
  nodes: preset.nodes,
  zoneBlocks: preset.zoneBlocks,
  roundabouts: preset.roundabouts,
  zoneCells: zoneCells,
  cars: [],
  simulationTime: 12.5
};

const view = Object.create(CityView3D.prototype);
view.sim = mockSim;

const mesh = new MeshData();
view.buildTerrainAndMountains(mesh);
const terrainIdx = mesh.indices.length;
console.log(`- 지형 및 산맥 메쉬 인덱스: ${terrainIdx}`);

view.buildRiverAndParks(mesh);
const riverIdx = mesh.indices.length - terrainIdx;
console.log(`- 생태 하천 및 수변공원 메쉬 인덱스: ${riverIdx}`);

view.buildRoadNetworkAndInterchange(mesh);
const roadIdx = mesh.indices.length - terrainIdx - riverIdx;
console.log(`- 도로망 및 입체교차로 메쉬 인덱스: ${roadIdx}`);

view.buildBenchmarkCentralCorridor(mesh);
const benchIdx = mesh.indices.length - terrainIdx - riverIdx - roadIdx;
console.log(`- 중앙 BRT 및 수변 기준구역 메쉬 인덱스: ${benchIdx}`);

view.buildRoundabouts(mesh);
const rbIdx = mesh.indices.length - terrainIdx - riverIdx - roadIdx - benchIdx;
console.log(`- 회전교차로 메쉬 인덱스: ${rbIdx}`);

view.buildHighQualityBuildings(mesh);
const bldIdx = mesh.indices.length - terrainIdx - riverIdx - roadIdx - benchIdx - rbIdx;
console.log(`- 고품질 건축 에셋 및 야외공간 메쉬 인덱스: ${bldIdx}`);

console.log(`총 정적 3D 메쉬 인덱스 수: ${mesh.indices.length}`);
assert.ok(mesh.indices.length > 200000, `충분한 고화질 디테일 확보 (${mesh.indices.length} > 200,000)`);

console.log('\n=== [3] 스펙큘러 및 반사광(Glass/Metal/Water) 채널 검증 ===');
let shinyVertexCount = 0;
let superShinyVertexCount = 0;
for (let i = 3; i < mesh.colors.length; i += 4) {
  const alpha = mesh.colors[i];
  if (alpha > 1.30) superShinyVertexCount++;
  else if (alpha > 1.05) shinyVertexCount++;
}
console.log(`- 스펙큘러/글래스 정점 수: ${shinyVertexCount + superShinyVertexCount}개 (초고광택: ${superShinyVertexCount})`);
assert.ok(shinyVertexCount + superShinyVertexCount > 1000, '다양한 재질 표현을 위한 스펙큘러 정점 충분성 확인');
console.log('✅ 블린-퐁 스페큘러 및 프레넬 광택 재질 메트릭 검증 통과');

console.log('\n=== [4] FootprintManager 충돌 방지 및 인동간격 무결성 보존 검증 ===');
const fp = view.footprintManager;
const buildings = fp.boxes.filter(b => b.tag.startsWith('building'));
const roads = fp.boxes.filter(b => b.tag === 'road');
const schools = fp.boxes.filter(b => b.tag === 'school');
const transits = fp.boxes.filter(b => b.tag === 'transit');
const rivers = fp.boxes.filter(b => b.tag === 'river');

console.log(`- 배치된 건축물 수: ${buildings.length}개`);
assert.ok(buildings.length >= 100, '충분한 건물 밀도 확보');

let buildingOverlaps = 0;
let minBuildingGap = Infinity;
for (let i = 0; i < buildings.length; i++) {
  for (let j = i + 1; j < buildings.length; j++) {
    const b1 = buildings[i];
    const b2 = buildings[j];
    if (b1.minX < b2.maxX && b1.maxX > b2.minX && b1.minY < b2.maxY && b1.maxY > b2.minY) {
      buildingOverlaps++;
    } else {
      const dx = Math.max(0, Math.max(b1.minX - b2.maxX, b2.minX - b1.maxX));
      const dy = Math.max(0, Math.max(b1.minY - b2.maxY, b2.minY - b1.maxY));
      const gap = Math.hypot(dx, dy);
      if (gap < minBuildingGap) minBuildingGap = gap;
    }
  }
}
assert.equal(buildingOverlaps, 0, '건물 상호 간 겹침 0건 보장');
assert.ok(minBuildingGap >= 6.0, `최소 인동간격 6.0m 보장 (실제: ${minBuildingGap.toFixed(2)}m)`);
console.log(`✅ 건물 상호 간 겹침 0건 및 인동 간격 보장 통과 (최소 간격: ${minBuildingGap.toFixed(2)}m)`);

let roadEncroachments = 0;
for (const b of buildings) {
  for (const r of roads) {
    if (b.minX < r.maxX && b.maxX > r.minX && b.minY < r.maxY && b.maxY > r.minY) {
      roadEncroachments++;
    }
  }
}
assert.equal(roadEncroachments, 0, '건물-도로 침범 0건 보장');
console.log('✅ 건물과 도로 간 침범 0건 검증 통과');

let facilityEncroachments = 0;
for (const b of buildings) {
  for (const f of [...schools, ...transits, ...rivers]) {
    if (b.minX < f.maxX && b.maxX > f.minX && b.minY < f.maxY && b.maxY > f.minY) {
      facilityEncroachments++;
    }
  }
}
assert.equal(facilityEncroachments, 0, '건물-특수시설 침범 0건 보장');
console.log('✅ 건물과 학교/환승센터/하천 특수부지 침범 0건 검증 통과');

console.log('\n=== [5] 10대 특화 건축 모델 다양성 분포 확인 ===');
const modelCounts = {};
for (const b of buildings) {
  const meta = b.meta || {};
  const key = `${b.tag}_M${meta.modelType}`;
  modelCounts[key] = (modelCounts[key] || 0) + 1;
}
console.log('건축물 모델별 다양성 분포:', modelCounts);
assert.ok(modelCounts['building_residential_M0'] > 0, '주거 와이드 판상형 M0');
assert.ok(modelCounts['building_residential_M1'] > 0, '주거 테라스 판상형 M1');
assert.ok(modelCounts['building_residential_M2'] > 0, '주거 파노라마 타워 M2');
assert.ok(modelCounts['building_residential_M3'] > 0, '주거 트윈 스카이브릿지 M3');
assert.ok(modelCounts['building_commercial_M0'] > 0, '상업 셋백 타워 M0');
assert.ok(modelCounts['building_commercial_M1'] > 0, '상업 로툰다 타워 M1');
assert.ok(modelCounts['building_commercial_M2'] > 0, '상업 트윈 복합몰 M2');
assert.ok(modelCounts['building_industrial_M0'] > 0, '연구 중정형 HQ M0');
assert.ok(modelCounts['building_industrial_M1'] > 0, '연구 L자형 테크랩 M1');
assert.ok(modelCounts['building_industrial_M2'] > 0, '연구 트윈 스카이워크 M2');
console.log('✅ 10대 특화 건축 모델 다양성 100% 확인');

console.log('\n=== [6] 동적 신호등 및 차량 렌더러 검증 ===');
const dynMesh = new MeshData();
view.renderSignals(dynMesh);
assert.ok(dynMesh.indices.length > 0, '동적 신호등 메쉬 생성됨');
console.log(`✅ 실시간 교차로 신호등 동적 렌더링 검증 통과 (인덱스: ${dynMesh.indices.length})`);

console.log('\n🎉 [SUCCESS] 3D 에셋 품질 고도화 및 발자국 무결성 자동 검증 완벽 통과! 🎉');
