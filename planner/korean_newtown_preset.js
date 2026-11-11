// 좌표와 길이는 미터 단위. z는 입체교차와 하천 횡단의 고도다.
function getIdealKoreanNewTownPresetData() {
  const nodes = [];
  const roads = [];
  const node = (name, x, y, z = 0) => {
    const result = { id: nodes.length + 1, name, x, y, z };
    nodes.push(result);
    return result;
  };
  const road = (from, to, type, name, options = {}) => {
    const defaults = {
      highway: { lanes: 8, speedLimit: 80 },
      arterial: { lanes: 4, speedLimit: 60 },
      local: { lanes: 2, speedLimit: 30 },
      parkway: { lanes: 1, speedLimit: 15 }
    };
    roads.push({
      id: roads.length + 1, from: from.id, to: to.id, type, name,
      ...defaults[type], ...options,
      length: Math.hypot(to.x - from.x, to.y - from.y, to.z - from.z),
      midPoint: null, trafficLoad: 0, recentCars: 0
    });
  };

  // 외곽 순환 고속도로와 고가 IC. 본선과 지상도로는 램프로만 연결된다.
  const nw = node('북서 고속도로', 0, 0, 8);
  const ni = node('북부 IC 본선', 1200, 0, 8);
  const ne = node('북동 고속도로', 2400, 0, 8);
  const ei = node('동부 IC 본선', 2400, 800, 8);
  const se = node('남동 고속도로', 2400, 1800, 8);
  const si = node('남부 IC 본선', 1200, 1800, 8);
  const sw = node('남서 고속도로', 0, 1800, 8);
  const wi = node('서부 IC 본선', 0, 800, 8);
  const ring = [nw, ni, ne, ei, se, si, sw, wi, nw];
  for (let i = 0; i < ring.length - 1; i++) {
    road(ring[i], ring[i + 1], 'highway', '외곽 순환 고속도로', { lanes: 4, speedLimit: 100, facility: 'expressway', gradeSeparated: true });
  }

  // 간선망은 모든 평면 교차 지점에서 노드를 공유한다.
  const rows = [400, 800, 1200, 1600];
  const columns = [400, 1200, 2000];
  const grid = rows.map((y, row) => columns.map((x, col) => node(`간선 교차로 ${row + 1}-${col + 1}`, x, y)));
  // 수변 북측·남측 교차로: 남북 BRT와 동서 간선의 2현시 신호.
  for (const crossing of [grid[1][1], grid[2][1]]) {
    crossing.signal = { cycle: 60, northSouthGreen: 35 };
  }
  for (let row = 0; row < grid.length; row++) {
    for (let col = 0; col < 2; col++) road(grid[row][col], grid[row][col + 1], 'arterial', '동서 보조간선');
  }
  for (let row = 0; row < grid.length - 1; row++) {
    road(grid[row][0], grid[row + 1][0], 'arterial', '서측 생활간선', { bridge: row === 1 });
    road(grid[row][1], grid[row + 1][1], 'highway', '중심 BRT 주간선', { facility: 'brt', brtLanes: 2, bridge: row === 1 });
    road(grid[row][2], grid[row + 1][2], 'arterial', '동측 테크노밸리 간선', { bridge: row === 1 });
  }

  // 단지 내부 순환도로는 건물 부지를 가로지르지 않고 네 간선 교차로와 연결된다.
  for (const [row, col, name] of [
    [0, 0, '서측 주거단지'], [0, 1, '동측 주거단지'],
    [2, 0, '중심상업지구'], [2, 1, '테크노밸리']
  ]) {
    const left = columns[col], right = columns[col + 1];
    const top = rows[row], bottom = rows[row + 1];
    const corners = [
      node(`${name} 북서 진입`, left + 32, top + 32),
      node(`${name} 북동 진입`, right - 32, top + 32),
      node(`${name} 남동 진입`, right - 32, bottom - 32),
      node(`${name} 남서 진입`, left + 32, bottom - 32)
    ];
    for (let i = 0; i < corners.length; i++) {
      road(corners[i], corners[(i + 1) % corners.length], 'local', `${name} 내부 순환도로`);
    }
    const entrances = [grid[row][col], grid[row][col + 1], grid[row + 1][col + 1], grid[row + 1][col]];
    for (let i = 0; i < corners.length; i++) road(entrances[i], corners[i], 'local', `${name} 연결도로`);
  }

  // 긴 슈퍼블록에 생활가로를 넣고, 접속점에서 기존 순환도로도 나눈다.
  for (const [left, name] of [[400, '서측 주거단지'], [1200, '동측 주거단지']]) {
    const intersections = [left + 32, left + 768].map(x => {
      const original = roads.find(r => r.name === `${name} 내부 순환도로` && (() => {
        const a = nodes.find(n => n.id === r.from), b = nodes.find(n => n.id === r.to);
        return a.x === x && b.x === x && Math.min(a.y, b.y) < 576 && Math.max(a.y, b.y) > 576;
      })());
      const end = nodes.find(n => n.id === original.to);
      const junction = node(`${name} 생활가로 접속`, x, 576);
      original.to = junction.id;
      const start = nodes.find(n => n.id === original.from);
      original.length = Math.hypot(junction.x - start.x, junction.y - start.y);
      road(junction, end, original.type, original.name);
      return junction;
    });
    road(intersections[0], intersections[1], 'local', `${name} 중앙 생활가로`, { facility: 'neighborhood' });
  }

  // 경사 램프의 접속점은 본선과 지상 간선에 각각 공유된다.
  const ramps = [
    [ni, grid[0][1], '북부 IC'], [ei, grid[1][2], '동부 IC'],
    [si, grid[3][1], '남부 IC'], [wi, grid[1][0], '서부 IC']
  ];
  for (const [from, to, name] of ramps) {
    road(from, to, 'local', `${name} 연결 램프`, { speedLimit: 40, facility: 'ramp', gradeSeparated: true });
  }

  // 남부 입체교차로 (Multi-level Interchange): 지상 관통 간선 및 고저차 다른 입체교차 램프
  const siGround = node('남부 IC 지상 하부교차로', 1200, 1800, 0);
  const siSouth = node('남부 도심외곽 연결로', 1200, 2020, 0);
  road(grid[3][1], siGround, 'arterial', '남부 간선 직진 하부도로', { facility: 'underpass', gradeSeparated: true });
  road(siGround, siSouth, 'arterial', '남부 광역 외곽연결로');

  const siEastPylon = node('남부 IC 동측 입체램프', 1420, 1740, 4);
  road(si, siEastPylon, 'local', '남부 IC 동측 감속램프', { speedLimit: 45, facility: 'interchange', gradeSeparated: true });
  road(siEastPylon, grid[3][1], 'local', '남부 IC 동측 합류램프', { speedLimit: 45, facility: 'interchange', gradeSeparated: true });

  const siWestPylon = node('남부 IC 서측 입체램프', 980, 1740, 4);
  road(grid[3][1], siWestPylon, 'local', '남부 IC 서측 진입램프', { speedLimit: 45, facility: 'interchange', gradeSeparated: true });
  road(siWestPylon, si, 'local', '남부 IC 서측 가속램프', { speedLimit: 45, facility: 'interchange', gradeSeparated: true });
  road(siEastPylon, siGround, 'local', '남부 IC 회전교차로 진출램프', { speedLimit: 35, facility: 'interchange', gradeSeparated: true });
  road(siGround, siWestPylon, 'local', '남부 IC 회전교차로 진입램프', { speedLimit: 35, facility: 'interchange', gradeSeparated: true });

  // 3단 고가 입체 플라이오버 (z=11m 최상층 오버패스)
  const flyoverWest = node('남부 플라이오버 서단', 1040, 1850, 7);
  const flyoverPeak = node('남부 플라이오버 정점', 1200, 1860, 11);
  const flyoverEast = node('남부 플라이오버 동단', 1360, 1850, 7);
  road(flyoverWest, flyoverPeak, 'local', '남부 입체 플라이오버 서측', { speedLimit: 50, facility: 'flyover', gradeSeparated: true });
  road(flyoverPeak, flyoverEast, 'local', '남부 입체 플라이오버 동측', { speedLimit: 50, facility: 'flyover', gradeSeparated: true });
  road(siWestPylon, flyoverWest, 'local', '남부 플라이오버 서측 연결램프', { speedLimit: 40, facility: 'flyover', gradeSeparated: true });
  road(flyoverEast, siEastPylon, 'local', '남부 플라이오버 동측 연결램프', { speedLimit: 40, facility: 'flyover', gradeSeparated: true });

  // 보행교와 강변길이 같은 노드를 공유한다. 자동차 교량과는 높이와 연결을 분리한다.
  const banks = [[944, '북안'], [1104, '남안']].map(([y, name]) => {
    const points = [240, 640, 1200, 1760, 2160].map(x =>
      node(`${name} 수변공원 ${x}m`, x, y, x === 640 || x === 1760 ? 2 : 0));
    for (let i = 0; i < points.length - 1; i++) {
      road(points[i], points[i + 1], 'parkway', `${name} 보행·자전거길`, { facility: 'pedestrian' });
    }
    return points;
  });
  road(banks[0][1], banks[1][1], 'parkway', '서측 생태수변 아치인도교', { facility: 'pedestrian_bridge', bridge: true });
  road(banks[0][3], banks[1][3], 'parkway', '동측 생태수변 아치인도교', { facility: 'pedestrian_bridge', bridge: true });

  // 기존 교차로에 접속한 도로 끝을 원형 노드로 옮겨, 실제 노드와 순환 도로를 갖춘 회전교차로(Roundabout)를 구성한다.
  const roundabouts = [
    { name: '서측 생활권', center: grid[1][0], x: grid[1][0].x, y: grid[1][0].y, radius: 24 },
    { name: '테크노밸리', center: grid[2][2], x: grid[2][2].x, y: grid[2][2].y, radius: 24 },
    { name: '남부 IC', center: siGround, x: siGround.x, y: siGround.y, radius: 70 }
  ];
  for (const rb of roundabouts) {
    const center = rb.center;
    const radius = rb.radius;
    const circle = Array.from({ length: 12 }, (_, i) => {
      const angle = i * Math.PI * 2 / 12;
      return node(`${rb.name} 회전교차로 ${i + 1}`, Math.round(center.x + radius * Math.cos(angle)), Math.round(center.y + radius * Math.sin(angle)));
    });
    const incident = roads.filter(r => r.from === center.id || r.to === center.id);
    for (const r of incident) {
      const other = nodes.find(n => n.id === (r.from === center.id ? r.to : r.from));
      const angle = Math.atan2(other.y - center.y, other.x - center.x);
      const index = (Math.round(angle * circle.length / (2 * Math.PI)) + circle.length) % circle.length;
      if (r.from === center.id) r.from = circle[index].id;
      else r.to = circle[index].id;
      const from = nodes.find(n => n.id === r.from);
      const to = nodes.find(n => n.id === r.to);
      r.length = Math.hypot(to.x - from.x, to.y - from.y, to.z - from.z);
    }
    for (let i = 0; i < circle.length; i++) {
      road(circle[i], circle[(i + 1) % circle.length], 'local', `${rb.name} 회전교차로`,
        { facility: 'roundabout', lanes: 2, speedLimit: 30, oneWay: true, roundaboutCenter: { x: rb.x, y: rb.y, radius: rb.radius } });
    }
  }
  for (const rb of roundabouts) nodes.splice(nodes.indexOf(rb.center), 1);

  // x/y는 좌상단, w/h는 크기. school 및 transit은 부지 용도 메타데이터다.
  // 주거 블록에서 학교 부지를 분리해 셀 변환 시 용도가 겹치지 않게 한다.
  const zoneBlocks = [
    { name: '서측 슈퍼블록 북부', type: 'residential', x: 464, y: 464, w: 672, h: 96, district: '서측 초품아' },
    { name: '서측 생활가로 남측', type: 'residential', x: 464, y: 592, w: 672, h: 16, district: '서측 초품아' },
    { name: '서측 슈퍼블록 서부', type: 'residential', x: 464, y: 608, w: 240, h: 128, district: '서측 초품아' },
    { name: '서측 초등학교 & 운동장', type: 'park', landUse: 'school', x: 704, y: 608, w: 192, h: 128, district: '서측 초품아', schoolName: '서온해람서초등학교', trackW: 108, trackH: 72 },
    { name: '서측 슈퍼블록 동부', type: 'residential', x: 896, y: 608, w: 240, h: 128, district: '서측 초품아' },
    { name: '동측 슈퍼블록 북부', type: 'residential', x: 1264, y: 464, w: 672, h: 96, district: '동측 초품아' },
    { name: '동측 생활가로 남측', type: 'residential', x: 1264, y: 592, w: 672, h: 16, district: '동측 초품아' },
    { name: '동측 슈퍼블록 서부', type: 'residential', x: 1264, y: 608, w: 240, h: 128, district: '동측 초품아' },
    { name: '동측 초등학교 & 운동장', type: 'park', landUse: 'school', x: 1504, y: 608, w: 192, h: 128, district: '동측 초품아', schoolName: '서온해람동초등학교', trackW: 108, trackH: 72 },
    { name: '동측 슈퍼블록 동부', type: 'residential', x: 1696, y: 608, w: 240, h: 128, district: '동측 초품아' },
    { name: '중심상업지구', type: 'commercial', x: 464, y: 1264, w: 576, h: 272 },
    { name: '중심복합환승센터', type: 'commercial', landUse: 'transit', x: 1056, y: 1264, w: 96, h: 272, facility: 'multimodal_transit', roof: 'aerofoil' },
    { name: '판교형 테크노밸리 R&D 캠퍼스', type: 'industrial', landUse: 'research', x: 1264, y: 1264, w: 672, h: 272 },
    { name: '수변생태공원 하천 축', type: 'park', landUse: 'river', x: 240, y: 960, w: 1920, h: 128, riverbed: true }
  ];

  return { cityName: '서온해람시', nodes, roads, zoneBlocks, roundabouts: roundabouts.map(r => ({ name: r.name, x: r.x, y: r.y, radius: r.radius })) };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getIdealKoreanNewTownPresetData };
  if (require.main === module) {
    const assert = require('node:assert/strict');
    const preset = getIdealKoreanNewTownPresetData();
    const ids = new Set(preset.nodes.map(n => n.id));
    assert.equal(ids.size, preset.nodes.length);
    assert(preset.roads.every(r => ids.has(r.from) && ids.has(r.to) && r.from !== r.to && r.length > 0));
    assert(preset.roads.some(r => r.facility === 'brt' && r.lanes === 8));
    assert.equal(preset.roads.filter(r => r.facility === 'ramp').length, 4);
    assert.equal(preset.roads.filter(r => r.name.endsWith('내부 순환도로')).length, 20);
    assert.equal(preset.zoneBlocks.filter(z => z.landUse === 'school').length, 2);
    assert(preset.zoneBlocks.some(z => z.landUse === 'transit'));
    assert(preset.zoneBlocks.some(z => z.landUse === 'research'));
    assert(preset.zoneBlocks.some(z => z.landUse === 'river'));
    assert(preset.zoneBlocks.every(z => z.w > 0 && z.h > 0));
    assert(preset.roads.some(r => r.facility === 'interchange'));
    assert(preset.roads.some(r => r.facility === 'flyover' && preset.nodes.find(n => n.id === r.to)?.z >= 11));
    assert(preset.roads.some(r => r.facility === 'pedestrian_bridge' && r.bridge));
    assert(preset.zoneBlocks.some(z => z.landUse === 'school' && z.trackW > 0));
    assert(preset.roads.some(r => r.facility === 'roundabout'));
    assert.equal(preset.roads.filter(r => r.facility === 'roundabout').length, 36);
    assert.ok(preset.roundabouts && preset.roundabouts.length >= 2);
    assert.notEqual(getIdealKoreanNewTownPresetData().nodes, preset.nodes);
    console.log('프리셋 검증 18개 통과 (회전교차로·입체교차·보행교·학교운동장·환승센터 포함)');
  }
}
