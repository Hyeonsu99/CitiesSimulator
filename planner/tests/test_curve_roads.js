const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = { window: { addEventListener() {} } };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'simulator.js'), 'utf8') + '\nthis.CitySimulator = CitySimulator;', context);
const sim = Object.create(context.CitySimulator.prototype);
Object.assign(sim, {
  nodes: [{ id: 1, x: 0, y: 0, z: 0 }, { id: 2, x: 200, y: 0, z: 10 }],
  roads: [], cars: [], roundabouts: [], selectedRoad: null, nextNodeId: 3, nextRoadId: 1,
  generateZoningGridForRoad() {}, updateStats() {}, notifyDataChanged() {}
});
const road = sim.createRoad(sim.nodes[0], sim.nodes[1], 'arterial', { x: 100, y: 100 });
road.lanes = 6; road.speedLimit = 45; road.facility = 'brt';
assert(road.length > 200 && road.length < 300);
assert.equal(sim.findRoadNear(100, 50, 3), road);
assert.equal(sim.findRoadNear(100, 0, 3), null);
const hit = sim.findRoadSplitPoint(100, 50, 3);
assert(hit && hit.road === road);
const originalQuarter = sim.roadPoint(road, 0.25);
const split = sim.splitRoadAt(road, hit.x, hit.y);
assert(Math.abs(split.x - 100) < 0.01 && Math.abs(split.y - 50) < 0.01);
assert(Math.abs(split.z - 5) < 0.01);
assert.equal(sim.roads.length, 2);
assert(sim.roads.every(r => r.lanes === 6 && r.speedLimit === 45 && r.facility === 'brt'));
const firstHalf = sim.roadPoint(sim.roads[0], 0.5);
assert(Math.hypot(firstHalf.x - originalQuarter.x, firstHalf.y - originalQuarter.y) < 0.01, '분할 후에도 원래 곡선이 유지되어야 함');
assert(sim.findRoadNear(100, 50, 3));
console.log('곡선 도로 선택·분할·고도·속성 보존 검증 통과');
