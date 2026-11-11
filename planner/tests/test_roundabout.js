const assert = require('node:assert/strict');
const { getIdealKoreanNewTownPresetData } = require('../korean_newtown_preset.js');
const { nodes, roads } = getIdealKoreanNewTownPresetData();
const ids = new Set(nodes.map(node => node.id));
assert.equal(ids.size, nodes.length);
assert(roads.every(road => ids.has(road.from) && ids.has(road.to) && road.length > 0));

const roundabouts = getIdealKoreanNewTownPresetData().roundabouts;
assert.equal(roundabouts.length, 3);
for (const roundabout of roundabouts) {
  const name = `${roundabout.name} 회전교차로`;
  const ring = roads.filter(road => road.name === name);
  assert.equal(ring.length, 12);
  assert(ring.every(road => road.facility === 'roundabout' && road.oneWay));
  const circle = new Set(ring.map(road => road.from));
  assert.equal(circle.size, 12);
  assert(ring.every(road => circle.has(road.to)));
  const entrances = roads.filter(road => !ring.includes(road) && !circle.has(road.from) && circle.has(road.to));
  const exits = roads.filter(road => !ring.includes(road) && circle.has(road.from) && !circle.has(road.to));
  assert(entrances.length > 0 && exits.length > 0);
  for (const entrance of entrances) {
    const reachable = new Set([entrance.to]);
    for (let i = 0; i < ring.length; i++) {
      for (const edge of ring) if (reachable.has(edge.from)) reachable.add(edge.to);
    }
    assert(exits.every(exit => reachable.has(exit.from)), `${name}: 진입 후 모든 출구에 도달해야 함`);
  }
}
console.log('회전교차로 3곳 연결 및 통행 방향 검증 통과');
