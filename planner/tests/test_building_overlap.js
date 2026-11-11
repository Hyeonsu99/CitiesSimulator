const assert = require('node:assert/strict');
const { getIdealKoreanNewTownPresetData } = require('../korean_newtown_preset.js');
const { CityView3D, FootprintManager, MeshData } = require('../view3d.js');

console.log('=== [1] FootprintManager 기본 단위 기능 검증 ===');
const fp = new FootprintManager();

// 기본 박스 등록 및 조회
fp.addBox(10, 10, 30, 30, 'road');
assert.equal(fp.boxes.length, 1);

// 충돌 감지 (여유 마진 포함)
assert.equal(fp.isOverlapping(25, 25, 40, 40), true, '겹치는 영역 감지 성공');
assert.equal(fp.isOverlapping(50, 50, 70, 70), false, '떨어진 영역 비충돌 감지 성공');

// 건물 간 인동 간격 마진(margin=6m) 검증
fp.addBox(100, 100, 150, 150, 'building_residential');
// 150 + 4 = 154 (이격거리 4m로 마진 6m 미달 -> 충돌로 판정되어야 함)
assert.equal(fp.isOverlapping(154, 100, 200, 150, 6.0), true, '인동 간격 미달(4m) 시 충돌 감지');
// 150 + 7 = 157 (이격거리 7m로 마진 6m 충족 -> 통과되어야 함)
assert.equal(fp.isOverlapping(157, 100, 200, 150, 6.0), false, '인동 간격 충족(7m) 시 통과');
console.log('✅ FootprintManager AABB 및 이격거리 계산 검증 통과');

console.log('\n=== [2] 신도시 조감도 건축 에셋 배치 및 발자국 무결성 검증 ===');
const preset = getIdealKoreanNewTownPresetData();

// 격자 셀 생성 (16m 단위)
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
  zoneCells: zoneCells
};

const view = Object.create(CityView3D.prototype);
view.sim = mockSim;

const mesh = new MeshData();
view.buildHighQualityBuildings(mesh);

const simFp = view.footprintManager;
assert.ok(simFp, 'CityView3D에 footprintManager 인스턴스 존재');

const buildings = simFp.boxes.filter(b => b.tag.startsWith('building'));
const roads = simFp.boxes.filter(b => b.tag === 'road');
const schools = simFp.boxes.filter(b => b.tag === 'school');
const transits = simFp.boxes.filter(b => b.tag === 'transit');
const rivers = simFp.boxes.filter(b => b.tag === 'river');

console.log(`- 배치된 건축물 수: ${buildings.length}개`);
console.log(`- 등록된 도로 발자국 박스 수: ${roads.length}개`);
console.log(`- 특수 랜드마크 부지: 학교 ${schools.length}개, 환승센터 ${transits.length}개, 하천 ${rivers.length}개`);

// 최소 건축물 수 보장 (신도시 조감도 스카이라인 형성)
assert.ok(buildings.length >= 100, `충분한 건물 밀도 확보 (${buildings.length} >= 100)`);

// 1. 건물 상호 간 겹침 0건 및 최소 인동 간격(>= 6.0m) 검증
let buildingOverlaps = 0;
let minBuildingGap = Infinity;

for (let i = 0; i < buildings.length; i++) {
  for (let j = i + 1; j < buildings.length; j++) {
    const b1 = buildings[i];
    const b2 = buildings[j];
    
    // AABB 겹침 체크
    const xOverlap = b1.minX < b2.maxX && b1.maxX > b2.minX;
    const yOverlap = b1.minY < b2.maxY && b1.maxY > b2.minY;
    if (xOverlap && yOverlap) {
      buildingOverlaps++;
    } else {
      // 분리된 경우 거리 계산
      const dx = Math.max(0, Math.max(b1.minX - b2.maxX, b2.minX - b1.maxX));
      const dy = Math.max(0, Math.max(b1.minY - b2.maxY, b2.minY - b1.maxY));
      const gap = Math.hypot(dx, dy);
      if (gap < minBuildingGap) minBuildingGap = gap;
    }
  }
}

assert.equal(buildingOverlaps, 0, `건물 상호 간 겹침은 0건이어야 함 (실제: ${buildingOverlaps})`);
assert.ok(minBuildingGap >= 6.0, `건물 간 최소 인동 간격은 6.0m 이상이어야 함 (실제: ${minBuildingGap.toFixed(2)}m)`);
console.log(`✅ 건물 상호 간 겹침 0건 및 인동 간격 보장 검증 통과 (최소 간격: ${minBuildingGap.toFixed(2)}m)`);

// 2. 건물과 도로 간 침범 0건 검증
let roadEncroachments = 0;
for (const b of buildings) {
  for (const r of roads) {
    if (b.minX < r.maxX && b.maxX > r.minX && b.minY < r.maxY && b.maxY > r.minY) {
      roadEncroachments++;
    }
  }
}
assert.equal(roadEncroachments, 0, `건물-도로 침범은 0건이어야 함 (실제: ${roadEncroachments})`);
console.log('✅ 건물과 도로 간 침범 0건 검증 통과 (도로 완충 구역 완벽 보호)');

// 3. 건물과 특수시설(학교, 환승센터, 하천) 침범 0건 검증
let facilityEncroachments = 0;
for (const b of buildings) {
  for (const f of [...schools, ...transits, ...rivers]) {
    if (b.minX < f.maxX && b.maxX > f.minX && b.minY < f.maxY && b.maxY > f.minY) {
      facilityEncroachments++;
    }
  }
}
assert.equal(facilityEncroachments, 0, `건물-특수시설 침범은 0건이어야 함 (실제: ${facilityEncroachments})`);
console.log('✅ 건물과 학교/환승센터/하천 특수부지 침범 0건 검증 통과');

// 4. 메쉬 정점 및 인덱스 생성 정상 동작 확인
assert.ok(mesh.positions.length > 0, '메쉬 정점 위치 생성됨');
assert.ok(mesh.normals.length > 0, '메쉬 법선 벡터 생성됨');
assert.ok(mesh.colors.length > 0, '메쉬 색상 생성됨');
assert.ok(mesh.indices.length > 0, '메쉬 인덱스 생성됨');
console.log(`✅ 3D 메쉬 데이터 무결성 검증 통과 (총 인덱스 수: ${mesh.indices.length})`);

// 5. 10대 특화 건축 모델 다양성(Diversity) 검증
const modelCounts = {};
for (const b of buildings) {
  const meta = b.meta || {};
  const key = `${b.tag}_M${meta.modelType}`;
  modelCounts[key] = (modelCounts[key] || 0) + 1;
}
console.log('건축물 모델별 다양성 분포:', modelCounts);
assert.ok(modelCounts['building_residential_M0'] > 0, '주거 와이드 판상형 M0 존재');
assert.ok(modelCounts['building_residential_M1'] > 0, '주거 테라스 판상형 M1 존재');
assert.ok(modelCounts['building_residential_M2'] > 0, '주거 파노라마 타워 M2 존재');
assert.ok(modelCounts['building_residential_M3'] > 0, '주거 트윈 스카이브릿지 M3 존재');
assert.ok(modelCounts['building_commercial_M0'] > 0, '상업 셋백 타워 M0 존재');
assert.ok(modelCounts['building_commercial_M1'] > 0, '상업 로툰다 타워 M1 존재');
assert.ok(modelCounts['building_commercial_M2'] > 0, '상업 트윈 복합몰 M2 존재');
assert.ok(modelCounts['building_industrial_M0'] > 0, '연구 중정형 HQ M0 존재');
assert.ok(modelCounts['building_industrial_M1'] > 0, '연구 L자형 테크랩 M1 존재');
assert.ok(modelCounts['building_industrial_M2'] > 0, '연구 트윈 스카이워크 M2 존재');
console.log('✅ 10대 특화 건축 모델 다양성 100% 충족 확인');

// 6. 구역 철거 / 동적 편집 시 유령 건물 배제 검증
const emptySim = {
  roads: preset.roads,
  nodes: preset.nodes,
  zoneBlocks: [],
  roundabouts: preset.roundabouts,
  zoneCells: new Map() // 모든 구역이 철거된 상태
};
const emptyView = Object.create(CityView3D.prototype);
emptyView.sim = emptySim;
const emptyMesh = new MeshData();
emptyView.buildHighQualityBuildings(emptyMesh);
const ghostBuildings = emptyView.footprintManager.boxes.filter(b => b.tag.startsWith('building'));
assert.equal(ghostBuildings.length, 0, '구역 철거 시 유령 건물 0개 보장');
console.log('✅ 구역 철거 및 편집 시 유령 건물 배제 무결성 통과');

console.log('\n🎉 모든 건물 발자국 충돌 방지 및 3D 에셋 검증 테스트 완벽 통과! 🎉');
