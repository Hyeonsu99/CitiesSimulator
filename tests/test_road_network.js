const assert = require('node:assert/strict');
const { nodes, roads, zoneBlocks } = require('../korean_newtown_preset.js').getIdealKoreanNewTownPresetData();
const byId = new Map(nodes.map(node => [node.id, node]));
assert.equal(byId.size, nodes.length);
assert(roads.every(road => byId.has(road.from) && byId.has(road.to) && road.length > 0));
const expressNode = nodes.find(node => node.name === '남부 IC 본선');
const interchange = roads.filter(road => road.name === '남부 IC 회전교차로');
const ringNodes = new Set(interchange.map(road => road.from));
assert.equal(interchange.length, 12);
assert([...ringNodes].every(id => byId.get(id).z === 0));
assert.equal(expressNode.z, 8);
assert(!ringNodes.has(expressNode.id), '고속도로 본선과 지상 로터리는 별도 레벨이어야 함');
const reachable = start => {
  const seen = new Set([start]);
  const queue = [start];
  while (queue.length) {
    const current = queue.shift();
    for (const road of roads) if (road.from === current && !seen.has(road.to)) {
      seen.add(road.to); queue.push(road.to);
    }
  }
  return seen;
};
assert([...ringNodes].some(id => reachable(expressNode.id).has(id)), '고속도로에서 진출 램프로 로터리에 진입해야 함');
assert(reachable(interchange[0].from).has(expressNode.id), '로터리에서 진입 램프로 고속도로에 진입해야 함');

for (const bridge of roads.filter(road => road.facility === 'pedestrian_bridge')) {
  for (const endpoint of [bridge.from, bridge.to]) {
    assert(roads.some(road => road.facility === 'pedestrian' && (road.from === endpoint || road.to === endpoint)), '보행교는 양쪽 강변길에 연결되어야 함');
  }
}
for (const name of ['남부 플라이오버 서측 연결램프', '남부 플라이오버 동측 연결램프']) {
  assert(roads.some(road => road.name === name));
}
const streets = roads.filter(road => road.facility === 'neighborhood');
assert.equal(streets.length, 2);
for (const street of streets) {
  const a = byId.get(street.from), b = byId.get(street.to);
  for (const endpoint of [a, b]) {
    assert(roads.some(road => road !== street && road.name.endsWith('내부 순환도로') && (road.from === endpoint.id || road.to === endpoint.id)));
  }
  assert(!zoneBlocks.some(zone => a.y > zone.y && a.y < zone.y + zone.h && Math.max(a.x, zone.x) < Math.min(b.x, zone.x + zone.w)), '생활가로가 건물 부지를 관통하면 안 됨');
}
console.log('생활가로·보행교·고가램프 연결 검증 통과');
