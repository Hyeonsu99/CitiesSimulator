const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = { window: { addEventListener() {} }, document: { getElementById: () => ({}) }, Math };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'simulator.js'), 'utf8') + '\nthis.CitySimulator = CitySimulator;', context);
const sim = Object.create(context.CitySimulator.prototype);
Object.assign(sim, { keys: {}, camera: { zoom: 1 }, isPlaying: true, simSpeed: 1,
  nodes: Array.from({ length: 15 }, (_, i) => ({ id: i, x: 0, y: i * 100 })),
  roads: Array.from({ length: 14 }, (_, i) => ({ from: i, to: i + 1, type: 'local', speedLimit: 30, length: i < 2 ? 5 : 100, trafficLoad: 0 })),
  cars: [], updateTrafficMeter() {} });
const random = Math.random;
try {
  Math.random = () => 0;
  sim.spawnCar();
  assert(sim.cars[0].path.length > 3, '짧은 도로의 경로가 조기에 끝나면 안 됨');
  Math.random = () => 1;
  sim.updateSimulation(100);
  assert.equal(sim.cars[0].roadIndex, 2);
  assert.equal(sim.cars[0].progress, 12.5, '도로를 여러 개 지나도 남은 거리를 보존해야 함');
  sim.roads = [{ from: 1, to: 2, type: 'parkway', length: 100 }];
  sim.cars = [];
  sim.spawnCar();
  assert.equal(sim.cars.length, 0, '보행로에서 자동차가 생성되면 안 됨');
  sim.nodes = [{ id: 1, x: 0, y: 0 }, { id: 2, x: 0, y: 100, signal: { cycle: 60, northSouthGreen: 35 } }, { id: 3, x: 0, y: 200 }];
  sim.roads = [{ id: 1, from: 1, to: 2, type: 'highway', facility: 'brt', length: 100, speedLimit: 30, trafficLoad: 0 },
    { id: 2, from: 2, to: 3, type: 'highway', facility: 'brt', length: 100, speedLimit: 30, trafficLoad: 0 }];
  sim.simulationTime = 40;
  sim.brtTimer = 0;
  sim.cars = [{ kind: 'car', roadIndex: 0, progress: 99, path: [1] }];
  sim.updateSimulation(100);
  assert.equal(sim.cars[0].roadIndex, 0, '적신호에 교차로를 통과하면 안 됨');
  sim.simulationTime = 0;
  sim.updateSimulation(100);
  assert.equal(sim.cars[0].roadIndex, 1, '녹색 신호에 통과해야 함');
  sim.cars = [];
  sim.spawnBrtBus();
  assert.equal(sim.cars[0].kind, 'bus');
  assert.deepEqual(Array.from(sim.cars[0].path), [1]);
  sim.cars[0].progress = 49;
  sim.updateSimulation(100);
  assert.equal(sim.cars[0].progress, 50, 'BRT 정류장에 정차해야 함');
  assert.equal(sim.cars[0].dwell, 5);
  sim.updateSimulation(100);
  assert.equal(sim.cars[0].progress, 50, '정차 시간 동안 움직이면 안 됨');
  sim.roads = [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }];
  sim.cars = [
    { roadIndex: 1, path: [2] },
    { roadIndex: 2, path: [3, 1, 0] },
    { roadIndex: 0, path: [2, 3] }
  ];
  sim.selectedRoad = null;
  sim.removeRoad(sim.roads[1]);
  assert.equal(sim.cars.length, 2, '삭제된 도로 위 차량은 제거해야 함');
  assert.equal(sim.cars[0].roadIndex, 1);
  assert.deepEqual(Array.from(sim.cars[0].path), [2], '삭제 도로 이후의 경로는 잘라야 함');
  assert.deepEqual(Array.from(sim.cars[1].path), [1, 2], '남은 도로 인덱스를 보정해야 함');
} finally {
  Math.random = random;
}
console.log('차량 경로·남은 이동 거리·보행로 검증 통과');
