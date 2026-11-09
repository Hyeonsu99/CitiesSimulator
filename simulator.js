// =======================================================================
// K-City Planner : 시티즈 2 스타일 도로망 & 구역 에디터 엔진 (simulator.js)
// =======================================================================

const ROAD_CONFIGS = {
  highway: { name: '주간선대로 (BRT 8차선)', lanes: 8, width: 28, maxSpeed: 80, color: '#f1c40f', capacity: 160 },
  arterial: { name: '보조간선대로 (4차선)', lanes: 4, width: 18, maxSpeed: 60, color: '#e67e22', capacity: 80 },
  local: { name: '생활집산도로 (2차선)', lanes: 2, width: 10, maxSpeed: 30, color: '#f8f9fa', capacity: 35 },
  parkway: { name: '선형 보행녹지축', lanes: 1, width: 6, maxSpeed: 15, color: '#2ecc71', capacity: 15 }
};

const ZONE_CONFIGS = {
  residential: { name: '아파트 슈퍼블록', color: '#e74c3c', fill: 'rgba(231, 76, 60, 0.75)', pop: 25, jobs: 1 },
  commercial: { name: '중심상업 & 환승센터', color: '#3498db', fill: 'rgba(52, 152, 219, 0.75)', pop: 2, jobs: 20 },
  industrial: { name: '테크노밸리 (R&D)', color: '#9b59b6', fill: 'rgba(155, 89, 182, 0.75)', pop: 0, jobs: 35 },
  park: { name: '수변생태공원', color: '#1abc9c', fill: 'rgba(26, 188, 156, 0.75)', pop: 0, jobs: 0 },
  dezone: { name: '구역 해제', color: 'transparent', fill: 'transparent', pop: 0, jobs: 0 }
};

class CitySimulator {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // 1. 카메라 뷰포트 (1 미터 단위)
    this.camera = { x: 750, y: 480, zoom: 0.85 };
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };
    this.cursorWorld = { x: 0, y: 0 };

    // 키보드 상태 (WASD)
    this.keys = {};

    // 2. 에디터 조작 상태
    this.currentCategory = 'roads'; // 'roads', 'zones', 'bulldoze'
    this.currentTool = 'road';
    this.currentType = 'highway';
    this.subMode = 'straight';      // 'straight', 'curve', 'move'

    // 스냅 옵션
    this.snapAngle = true;
    this.snapGrid = true;
    this.snapRoad = true;

    // 드로잉 인터랙션 상태
    this.roadStartNode = null;
    this.roadMidPoint = null;        // 3점 곡선 모드용 경유점
    this.hoveredRoad = null;
    this.hoveredNode = null;
    this.draggedNode = null;         // Move It 모드용
    this.selectedRoad = null;
    this.isPaintingZone = false;

    // 3. 데이터 모델
    this.nodes = [];                 // { id, x, y, z }
    this.roads = [];                 // { id, from, to, type, lanes, speedLimit, length, cp1, cp2, trafficLoad }
    this.zoneCells = new Map();      // key: `${x},${y}` -> { x, y, type, landUse, name } (시티즈 2 스타일 16m 격자 셀)
    this.zoneBlocks = [];            // 특수 랜드마크 블록 (학교·운동장, 환승센터, 하천 등)
    this.roundabouts = [];           // 원형 회전교차로 목록 { name, x, y, radius }
    this.cars = [];                  // 실시간 시뮬레이션 차량
    this.nextNodeId = 1;
    this.nextRoadId = 1;

    // 4. 2D / 3D 뷰 모드
    this.viewMode = '2d';            // '2d' | '3d'
    this.view3D = null;              // CityView3D 인스턴스

    // 5. 시뮬레이션 루프
    this.isPlaying = true;
    this.simSpeed = 1;
    this.lastFrameTime = performance.now();
    this.simulationTime = 0;
    this.brtTimer = 0;

    this.initCanvasSize();
    this.bindEvents();
    // this.loadIdealKoreanNewTownPreset(); // 시작 시 빈 화면
    this.loop();
  }

  initCanvasSize() {
    this.canvas.width = this.canvas.parentElement.clientWidth;
    this.canvas.height = this.canvas.parentElement.clientHeight;
  }

  toggleViewMode() {
    this.setViewMode(this.viewMode === '2d' ? '3d' : '2d');
  }

  setViewMode(mode) {
    this.viewMode = mode;
    const simCanvas = this.canvas;
    const canvas3D = document.getElementById('simCanvas3D');
    const hud3D = document.getElementById('hud-3d-controls');
    const subbar2D = document.querySelector('.tool-subbar');
    const overlayTop2D = document.querySelector('.canvas-overlay-top');
    const btnToggle = document.getElementById('btn-toggle-view');

    if (mode === '3d') {
      simCanvas.style.display = 'none';
      if (canvas3D) canvas3D.style.display = 'block';
      if (hud3D) hud3D.style.display = 'flex';
      if (subbar2D) subbar2D.style.display = 'none';
      if (overlayTop2D) overlayTop2D.style.display = 'none';

      if (btnToggle) {
        btnToggle.innerHTML = '🗺️ 2D 편집 모드';
        btnToggle.classList.add('mode-3d-active');
      }

      if (!this.view3D && typeof CityView3D === 'function' && canvas3D) {
        this.view3D = new CityView3D(this, canvas3D);
      }
      if (this.view3D) {
        this.view3D.resize();
        this.view3D.markDirty();
      }
    } else {
      if (canvas3D) canvas3D.style.display = 'none';
      simCanvas.style.display = 'block';
      if (hud3D) hud3D.style.display = 'none';
      if (subbar2D) subbar2D.style.display = 'flex';
      if (overlayTop2D) overlayTop2D.style.display = 'flex';

      if (btnToggle) {
        btnToggle.innerHTML = '🏙️ 3D 조감도';
        btnToggle.classList.remove('mode-3d-active');
      }

      this.initCanvasSize();
    }
  }

  notifyDataChanged() {
    if (this.view3D) {
      this.view3D.markDirty();
    }
  }

  // -------------------------------------------------------------------
  // 이벤트 바인딩 (키보드, 마우스, UI 연동)
  // -------------------------------------------------------------------
  bindEvents() {
    window.addEventListener('resize', () => this.initCanvasSize());

    // WASD 키보드 입력 및 Tab/V 뷰 전환
    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
      if (e.key === 'Tab' || (e.key.toLowerCase() === 'v' && e.target.tagName !== 'INPUT')) {
        e.preventDefault();
        this.toggleViewMode();
      }
    });
    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
    });

    // 캔버스 마우스 조작
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
    this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());

    // 상단 버튼들
    const btnToggle = document.getElementById('btn-toggle-view');
    if (btnToggle) btnToggle.addEventListener('click', () => this.toggleViewMode());
    document.getElementById('btn-preset').addEventListener('click', () => this.loadIdealKoreanNewTownPreset());
    document.getElementById('btn-clear').addEventListener('click', () => this.clearAll());
    document.getElementById('btn-export').addEventListener('click', () => this.exportCS2());

    // 3D 조감도 HUD 컨트롤 바인딩
    const bind3D = (id, fn) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('click', fn);
    };

    const setPresetActive = (btnId) => {
      ['view-preset-south', 'view-preset-iso', 'view-preset-low', 'view-preset-top'].forEach(id => {
        const b = document.getElementById(id);
        if (b) b.classList.remove('active');
      });
      const activeBtn = document.getElementById(btnId);
      if (activeBtn) activeBtn.classList.add('active');
    };

    bind3D('view-preset-south', () => { if (this.view3D) { this.view3D.setPresetView('south'); setPresetActive('view-preset-south'); } });
    bind3D('view-preset-iso', () => { if (this.view3D) { this.view3D.setPresetView('isometric'); setPresetActive('view-preset-iso'); } });
    bind3D('view-preset-low', () => { if (this.view3D) { this.view3D.setPresetView('low'); setPresetActive('view-preset-low'); } });
    bind3D('view-preset-top', () => { if (this.view3D) { this.view3D.setPresetView('top'); setPresetActive('view-preset-top'); } });

    bind3D('btn-cam-rotate-left', () => { if (this.view3D) this.view3D.camera.yaw -= 0.15; });
    bind3D('btn-cam-rotate-right', () => { if (this.view3D) this.view3D.camera.yaw += 0.15; });
    bind3D('btn-cam-tilt-up', () => { if (this.view3D) this.view3D.camera.pitch = Math.min(1.48, this.view3D.camera.pitch + 0.1); });
    bind3D('btn-cam-tilt-down', () => { if (this.view3D) this.view3D.camera.pitch = Math.max(0.18, this.view3D.camera.pitch - 0.1); });
    bind3D('btn-cam-zoom-in', () => { if (this.view3D) this.view3D.camera.distance = Math.max(220, this.view3D.camera.distance * 0.85); });
    bind3D('btn-cam-zoom-out', () => { if (this.view3D) this.view3D.camera.distance = Math.min(3600, this.view3D.camera.distance * 1.18); });
    bind3D('btn-cam-autorotate', () => {
      if (this.view3D) {
        const isRotating = this.view3D.toggleAutoRotate();
        const btn = document.getElementById('btn-cam-autorotate');
        if (btn) btn.classList.toggle('active', isRotating);
      }
    });
    bind3D('btn-3d-exit', () => this.toggleViewMode());

    // 서브모드 버튼 (직선 / 곡선 / Move It)
    document.querySelectorAll('.sub-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.sub-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.subMode = btn.dataset.submode;
        this.resetDrawingState();
      });
    });

    // 스냅 체크박스
    const angleChk = document.getElementById('snap-angle');
    if (angleChk) angleChk.addEventListener('change', (e) => this.snapAngle = e.target.checked);
    const gridChk = document.getElementById('snap-grid');
    if (gridChk) gridChk.addEventListener('change', (e) => this.snapGrid = e.target.checked);
    const roadChk = document.getElementById('snap-road');
    if (roadChk) roadChk.addEventListener('change', (e) => this.snapRoad = e.target.checked);

    // 하단 카테고리 탭 (도로 / 구역 / 철거)
    document.querySelectorAll('.dock-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.dock-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const cat = tab.dataset.category;
        this.currentCategory = cat;

        document.getElementById('items-roads').style.display = (cat === 'roads') ? 'flex' : 'none';
        document.getElementById('items-zones').style.display = (cat === 'zones') ? 'flex' : 'none';
        document.getElementById('items-bulldoze').style.display = (cat === 'bulldoze') ? 'flex' : 'none';

        if (cat === 'bulldoze') {
          this.currentTool = 'bulldoze';
        } else if (cat === 'roads') {
          this.currentTool = 'road';
          const activeItem = document.querySelector('#items-roads .tool-item.active');
          this.currentType = activeItem ? activeItem.dataset.type : 'highway';
        } else if (cat === 'zones') {
          this.currentTool = 'zone';
          const activeItem = document.querySelector('#items-zones .tool-item.active');
          this.currentType = activeItem ? activeItem.dataset.type : 'residential';
        }
        this.resetDrawingState();
      });
    });

    // 하단 툴 아이템 (차종 / 구역종류 선택)
    document.querySelectorAll('.tool-item').forEach(item => {
      item.addEventListener('click', () => {
        const parent = item.parentElement;
        parent.querySelectorAll('.tool-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        this.currentTool = item.dataset.tool;
        this.currentType = item.dataset.type;
        this.resetDrawingState();
      });
    });

    // 시뮬레이션 제어
    const playBtn = document.getElementById('btn-play');
    playBtn.addEventListener('click', () => {
      this.isPlaying = !this.isPlaying;
      playBtn.textContent = this.isPlaying ? '⏸ 일시정지' : '▶ 재생';
      playBtn.classList.toggle('paused', !this.isPlaying);
    });

    document.querySelectorAll('.btn-speed').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.simSpeed = parseFloat(btn.dataset.speed);
      });
    });

    // 인스펙터 차선 확장
    document.getElementById('btn-upgrade-lane').addEventListener('click', () => {
      if (this.selectedRoad && this.selectedRoad.lanes < 12) {
        this.selectedRoad.lanes += 2;
        this.updateInspector();
        this.notifyDataChanged();
      }
    });
    document.getElementById('btn-downgrade-lane').addEventListener('click', () => {
      if (this.selectedRoad && this.selectedRoad.lanes > 2) {
        this.selectedRoad.lanes -= 2;
        this.updateInspector();
        this.notifyDataChanged();
      }
    });
  }

  resetDrawingState() {
    this.roadStartNode = null;
    this.roadMidPoint = null;
    this.draggedNode = null;
    this.isPaintingZone = false;
    this.hideHUD();
  }

  // -------------------------------------------------------------------
  // 좌표계 변환 및 스냅 수학
  // -------------------------------------------------------------------
  screenToWorld(sx, sy) {
    return {
      x: (sx - this.canvas.width / 2) / this.camera.zoom + this.camera.x,
      y: (sy - this.canvas.height / 2) / this.camera.zoom + this.camera.y
    };
  }

  worldToScreen(wx, wy) {
    return {
      x: (wx - this.camera.x) * this.camera.zoom + this.canvas.width / 2,
      y: (wy - this.camera.y) * this.camera.zoom + this.canvas.height / 2
    };
  }

  getSnappedPos(rawX, rawY, fromNode = null) {
    let x = rawX;
    let y = rawY;

    // 1. 기존 노드 근처면 자동 결합 스냅 (우선순위 최고)
    const nearNode = this.findNearestNode(rawX, rawY, 25);
    if (nearNode && (!fromNode || nearNode.id !== fromNode.id)) {
      return { x: nearNode.x, y: nearNode.y, targetNode: nearNode, isRoadSplit: false };
    }

    // 2. 도로 선분 위 교차로 자동 분할 스냅 (Road Split)
    if (this.snapRoad && this.currentCategory === 'roads') {
      const splitInfo = this.findRoadSplitPoint(rawX, rawY, 20);
      if (splitInfo) {
        return { x: splitInfo.x, y: splitInfo.y, targetNode: null, isRoadSplit: true, splitRoad: splitInfo.road };
      }
    }

    // 3. 각도 스냅 (직선 모드에서 90도, 45도 스냅)
    if (this.snapAngle && fromNode) {
      const dx = rawX - fromNode.x;
      const dy = rawY - fromNode.y;
      const dist = Math.hypot(dx, dy);
      let angle = Math.atan2(dy, dx); // 라디안
      const snapDegs = [0, 45, 90, 135, 180, -45, -90, -135, -180];
      const curDeg = angle * (180 / Math.PI);

      for (const targetDeg of snapDegs) {
        if (Math.abs(curDeg - targetDeg) < 8) {
          angle = targetDeg * (Math.PI / 180);
          x = fromNode.x + Math.cos(angle) * dist;
          y = fromNode.y + Math.sin(angle) * dist;
          break;
        }
      }
    }

    // 4. 기본 그리드 스냅 (50m 단위)
    if (this.snapGrid) {
      x = Math.round(x / 50) * 50;
      y = Math.round(y / 50) * 50;
    }

    return { x, y, targetNode: null, isRoadSplit: false };
  }

  findNearestNode(wx, wy, maxDist = 25) {
    let nearest = null;
    let minDist = maxDist;
    for (const node of this.nodes) {
      const d = Math.hypot(node.x - wx, node.y - wy);
      if (d < minDist) {
        minDist = d;
        nearest = node;
      }
    }
    return nearest;
  }

  findRoadSplitPoint(wx, wy, maxDist = 20) {
    for (const road of this.roads) {
      const fNode = this.nodes.find(n => n.id === road.from);
      const tNode = this.nodes.find(n => n.id === road.to);
      if (!fNode || !tNode) continue;

      const p = this.closestPointOnRoad(road, wx, wy);
      const d = Math.hypot(wx - p.x, wy - p.y);
      // 양 끝점(노드)과는 30m 이상 떨어져 있어야 중간 분할
      const dToF = Math.hypot(p.x - fNode.x, p.y - fNode.y);
      const dToT = Math.hypot(p.x - tNode.x, p.y - tNode.y);
      if (d < maxDist && dToF > 30 && dToT > 30) {
        return { x: p.x, y: p.y, road: road };
      }
    }
    return null;
  }

  closestPointOnSegment(px, py, x1, y1, x2, y2) {
    const l2 = (x2 - x1)**2 + (y2 - y1)**2;
    if (l2 === 0) return { x: x1, y: y1 };
    let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
    t = Math.max(0, Math.min(1, t));
    return { x: x1 + t * (x2 - x1), y: y1 + t * (y2 - y1) };
  }

  roadPoint(road, t) {
    const a = this.nodes.find(n => n.id === road.from);
    const b = this.nodes.find(n => n.id === road.to);
    if (!a || !b) return null;
    const c = road.midPoint;
    return c ? { x: (1-t)**2*a.x + 2*(1-t)*t*c.x + t*t*b.x, y: (1-t)**2*a.y + 2*(1-t)*t*c.y + t*t*b.y }
      : { x: a.x + (b.x-a.x)*t, y: a.y + (b.y-a.y)*t };
  }

  roadLength(road) {
    let prev = this.roadPoint(road, 0), length = 0;
    if (!prev) return 0;
    const steps = road.midPoint ? 32 : 1;
    for (let i = 1; i <= steps; i++) {
      const point = this.roadPoint(road, i / steps);
      length += Math.hypot(point.x - prev.x, point.y - prev.y);
      prev = point;
    }
    return length;
  }

  closestPointOnRoad(road, x, y) {
    // ponytail: 32-segment curve approximation; adaptive subdivision if very large curves need greater accuracy.
    const steps = road.midPoint ? 32 : 1;
    let best = null, distance = Infinity, prev = this.roadPoint(road, 0);
    if (!prev) return null;
    for (let i = 1; i <= steps; i++) {
      const next = this.roadPoint(road, i / steps);
      const dx = next.x - prev.x, dy = next.y - prev.y, len2 = dx*dx + dy*dy;
      const fraction = len2 ? Math.max(0, Math.min(1, ((x-prev.x)*dx + (y-prev.y)*dy) / len2)) : 0;
      const px = prev.x + fraction*dx, py = prev.y + fraction*dy;
      const d = Math.hypot(x-px, y-py);
      if (d < distance) { distance = d; best = { ...this.roadPoint(road, (i - 1 + fraction) / steps), t: (i - 1 + fraction) / steps }; }
      prev = next;
    }
    return best;
  }

  // -------------------------------------------------------------------
  // 마우스 조작 핸들러
  // -------------------------------------------------------------------
  onMouseDown(e) {
    // 마우스 우클릭 / 휠클릭 -> 화면 패닝
    if (e.button === 2 || e.button === 1) {
      this.isPanning = true;
      this.panStart = { x: e.clientX, y: e.clientY };
      return;
    }

    if (e.button === 0) {
      const w = this.screenToWorld(e.clientX - this.canvas.offsetLeft, e.clientY - this.canvas.offsetTop);

      // A. Move It 모드 (노드 드래그 이동)
      if (this.subMode === 'move') {
        const node = this.findNearestNode(w.x, w.y, 30);
        if (node) {
          this.draggedNode = node;
        }
        return;
      }

      // B. 철거(Bulldoze) 모드
      if (this.currentCategory === 'bulldoze') {
        this.performBulldoze(w.x, w.y);
        return;
      }

      // C. 구역(Zoning) 브러시 모드
      if (this.currentCategory === 'zones') {
        this.isPaintingZone = true;
        this.paintZoneCellAt(w.x, w.y);
        return;
      }

      // D. 도로 건설 모드
      if (this.currentCategory === 'roads') {
        const snapped = this.getSnappedPos(w.x, w.y, this.roadStartNode);

        // 첫 번째 클릭: 시작 노드 생성 또는 기존 노드 선택
        if (!this.roadStartNode) {
          if (snapped.targetNode) {
            this.roadStartNode = snapped.targetNode;
          } else if (snapped.isRoadSplit) {
            // 도로 중간 분할 노드 생성
            this.roadStartNode = this.splitRoadAt(snapped.splitRoad, snapped.x, snapped.y);
          } else {
            const newNode = { id: this.nextNodeId++, x: snapped.x, y: snapped.y };
            this.nodes.push(newNode);
            this.roadStartNode = newNode;
          }
          return;
        }

        // 두 번째 클릭: 곡선 모드일 때 경유점 지정
        if (this.subMode === 'curve' && !this.roadMidPoint) {
          this.roadMidPoint = { x: snapped.x, y: snapped.y };
          return;
        }

        // 끝점 클릭: 도로 생성 완료
        let endNode = snapped.targetNode;
        if (!endNode) {
          if (snapped.isRoadSplit) {
            endNode = this.splitRoadAt(snapped.splitRoad, snapped.x, snapped.y);
          } else {
            endNode = { id: this.nextNodeId++, x: snapped.x, y: snapped.y };
            this.nodes.push(endNode);
          }
        }

        if (this.roadStartNode.id !== endNode.id) {
          this.createRoad(this.roadStartNode, endNode, this.currentType, this.roadMidPoint);
        }

        // 다음 도로 연속 그리기
        this.roadStartNode = endNode;
        this.roadMidPoint = null;
        this.hideHUD();
      }
    }
  }

  onMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const w = this.screenToWorld(sx, sy);
    this.cursorWorld = w;
    document.getElementById('cursorPos').textContent = `X: ${Math.round(w.x)}m, Y: ${Math.round(w.y)}m`;

    // 1. 화면 패닝
    if (this.isPanning) {
      const dx = (e.clientX - this.panStart.x) / this.camera.zoom;
      const dy = (e.clientY - this.panStart.y) / this.camera.zoom;
      this.camera.x -= dx;
      this.camera.y -= dy;
      this.panStart = { x: e.clientX, y: e.clientY };
      return;
    }

    // 2. Move It 노드 드래그
    if (this.draggedNode) {
      const snapped = this.getSnappedPos(w.x, w.y);
      const dx = snapped.x - this.draggedNode.x;
      const dy = snapped.y - this.draggedNode.y;
      for (const road of this.roads) {
        if (road.midPoint && (road.from === this.draggedNode.id || road.to === this.draggedNode.id)) {
          road.midPoint.x += dx / 2;
          road.midPoint.y += dy / 2;
        }
      }
      this.draggedNode.x = snapped.x;
      this.draggedNode.y = snapped.y;
      this.updateRoadLengths();
      return;
    }

    // 3. 구역(Zoning) 연속 드래그 색칠
    if (this.isPaintingZone && this.currentCategory === 'zones') {
      this.paintZoneCellAt(w.x, w.y);
      return;
    }

    // 4. 호버 감지 (철거 하이라이트 & 노드/도로 인스펙션)
    this.hoveredNode = this.findNearestNode(w.x, w.y, 20);
    this.hoveredRoad = this.findRoadNear(w.x, w.y, 18);

    // 5. 도로 그리기 HUD 갱신 (길이 및 각도 표시)
    if (this.currentCategory === 'roads' && this.roadStartNode) {
      const snapped = this.getSnappedPos(w.x, w.y, this.roadStartNode);
      const dx = snapped.x - this.roadStartNode.x;
      const dy = snapped.y - this.roadStartNode.y;
      const dist = Math.round(Math.hypot(dx, dy));
      let deg = Math.round(Math.atan2(-dy, dx) * (180 / Math.PI));
      if (deg < 0) deg += 360;

      this.showHUD(sx, sy, dist, deg);
    } else {
      this.hideHUD();
    }
  }

  onMouseUp(e) {
    if (e.button === 2 || e.button === 1) {
      this.isPanning = false;
      return;
    }

    if (e.button === 0) {
      if (this.draggedNode) {
        this.notifyDataChanged();
      }
      this.draggedNode = null;
      this.isPaintingZone = false;
    }
  }

  onWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    const newZoom = Math.min(Math.max(this.camera.zoom * zoomFactor, 0.25), 3.0);
    this.camera.zoom = newZoom;
  }

  showHUD(sx, sy, length, angle) {
    const hud = document.getElementById('road-hud');
    hud.style.display = 'flex';
    hud.style.left = `${sx + 15}px`;
    hud.style.top = `${sy + 15}px`;
    document.getElementById('hud-length').textContent = `${length}m`;
    document.getElementById('hud-angle').textContent = `${angle}°`;
  }

  hideHUD() {
    const hud = document.getElementById('road-hud');
    if (hud) hud.style.display = 'none';
  }

  // -------------------------------------------------------------------
  // 도로 관리 및 T자 교차로 분할 (Road Split)
  // -------------------------------------------------------------------
  createRoad(fromNode, toNode, type, midPoint = null) {
    const cfg = ROAD_CONFIGS[type] || ROAD_CONFIGS.arterial;
    const road = {
      id: this.nextRoadId++,
      from: fromNode.id,
      to: toNode.id,
      type: type,
      lanes: cfg.lanes,
      speedLimit: cfg.maxSpeed,
      length: 0,
      midPoint: midPoint ? { x: midPoint.x, y: midPoint.y } : null,
      trafficLoad: 0,
      recentCars: 0
    };
    road.length = this.roadLength(road);

    this.roads.push(road);
    this.generateZoningGridForRoad(road);
    this.updateStats();
    this.notifyDataChanged();
    return road;
  }

  splitRoadAt(road, splitX, splitY) {
    const fNode = this.nodes.find(n => n.id === road.from);
    const tNode = this.nodes.find(n => n.id === road.to);
    
    const hit = this.closestPointOnRoad(road, splitX, splitY);
    if (!hit || !fNode || !tNode) return null;
    const t = hit.t;
    const splitNode = { id: this.nextNodeId++, x: hit.x, y: hit.y,
      z: (fNode.z || 0) + ((tNode.z || 0) - (fNode.z || 0)) * t };
    this.nodes.push(splitNode);

    const c = road.midPoint;
    const firstControl = c && { x: fNode.x + (c.x - fNode.x) * t, y: fNode.y + (c.y - fNode.y) * t };
    const secondControl = c && { x: c.x + (tNode.x - c.x) * t, y: c.y + (tNode.y - c.y) * t };
    const roundabouts = this.roundabouts;

    // 기존 도로 제거 후 2개로 분할 연결
    this.removeRoad(road);

    this.roundabouts = roundabouts;
    const first = this.createRoad(fNode, splitNode, road.type, firstControl);
    const second = this.createRoad(splitNode, tNode, road.type, secondControl);
    const { id, from, to, midPoint, length, ...properties } = road;
    Object.assign(first, properties);
    Object.assign(second, properties);

    return splitNode;
  }

  removeRoad(road) {
    const index = this.roads.indexOf(road);
    if (index < 0) return;
    this.roads.splice(index, 1);
    // 경로는 도로 배열 인덱스이므로 삭제된 도로 뒤의 인덱스를 함께 이동한다.
    this.cars = this.cars.filter(car => car.roadIndex !== index);
    for (const car of this.cars) {
      if (car.roadIndex > index) car.roadIndex--;
      const path = car.path || [];
      const deletedAt = path.indexOf(index);
      car.path = (deletedAt < 0 ? path : path.slice(0, deletedAt))
        .map(item => item > index ? item - 1 : item);
    }
    if (this.selectedRoad === road) {
      this.selectedRoad = null;
      this.updateInspector();
    }
    if (road.facility === 'roundabout' && road.roundaboutCenter) {
      const { x, y } = road.roundaboutCenter;
      this.roundabouts = (this.roundabouts || []).filter(item => item.x !== x || item.y !== y);
    }
  }

  updateRoadLengths() {
    for (const r of this.roads) {
      const fNode = this.nodes.find(n => n.id === r.from);
      const tNode = this.nodes.find(n => n.id === r.to);
      if (fNode && tNode) {
        r.length = this.roadLength(r);
      }
    }
  }

  findRoadNear(wx, wy, maxDist = 20) {
    for (const r of this.roads) {
      const fNode = this.nodes.find(n => n.id === r.from);
      const tNode = this.nodes.find(n => n.id === r.to);
      if (!fNode || !tNode) continue;
      const p = this.closestPointOnRoad(r, wx, wy);
      if (Math.hypot(wx - p.x, wy - p.y) < maxDist) {
        return r;
      }
    }
    return null;
  }

  performBulldoze(wx, wy) {
    // 1. 도로 철거
    const r = this.findRoadNear(wx, wy, 25);
    if (r) {
      this.removeRoad(r);
      this.updateStats();
      this.notifyDataChanged();
      return;
    }

    // 2. 구역 셀 철거
    const cellSize = 16;
    const cx = Math.floor(wx / cellSize) * cellSize;
    const cy = Math.floor(wy / cellSize) * cellSize;
    const key = `${cx},${cy}`;
    if (this.zoneCells.has(key)) {
      this.zoneCells.delete(key);
      this.updateStats();
      this.notifyDataChanged();
    }
  }

  // -------------------------------------------------------------------
  // 시티즈 2 스타일 도로변 격자(Zoning Grid) 자동 생성 & 브러시 채색
  // -------------------------------------------------------------------
  generateZoningGridForRoad(road) {
    const fNode = this.nodes.find(n => n.id === road.from);
    const tNode = this.nodes.find(n => n.id === road.to);
    if (!fNode || !tNode) return;

    const len = this.roadLength(road);
    if (len === 0) return;
    const roadWidth = (ROAD_CONFIGS[road.type].width || 14) / 2;
    const cellSize = 16; // 16m 격자 셀

    // 도로 양옆 4셀 너비 격자 등록
    for (let d = 16; d < len - 16; d += cellSize) {
      const t = d / len;
      const point = this.roadPoint(road, t);
      const before = this.roadPoint(road, Math.max(0, t - 0.001));
      const after = this.roadPoint(road, Math.min(1, t + 0.001));
      const dx = after.x - before.x, dy = after.y - before.y;
      const tangent = Math.hypot(dx, dy);
      if (!tangent) continue;
      const nx = -dy / tangent, ny = dx / tangent;
      const px = point.x, py = point.y;

      for (const side of [-1, 1]) {
        for (let row = 1; row <= 4; row++) {
          const gx = Math.round((px + nx * side * (roadWidth + row * cellSize - cellSize / 2)) / cellSize) * cellSize;
          const gy = Math.round((py + ny * side * (roadWidth + row * cellSize - cellSize / 2)) / cellSize) * cellSize;
          const key = `${gx},${gy}`;
          if (!this.zoneCells.has(key)) {
            this.zoneCells.set(key, { x: gx, y: gy, type: null }); // 빈 격자 셀 등록
          }
        }
      }
    }
  }

  paintZoneCellAt(wx, wy) {
    const cellSize = 16;
    const cx = Math.round(wx / cellSize) * cellSize;
    const cy = Math.round(wy / cellSize) * cellSize;
    const brushRadius = 32; // 브러시 반경 32m

    for (let x = cx - brushRadius; x <= cx + brushRadius; x += cellSize) {
      for (let y = cy - brushRadius; y <= cy + brushRadius; y += cellSize) {
        const key = `${x},${y}`;
        if (this.currentType === 'dezone') {
          if (this.zoneCells.has(key)) {
            const cell = this.zoneCells.get(key);
            cell.type = null;
          }
        } else {
          this.zoneCells.set(key, { x: x, y: y, type: this.currentType });
        }
      }
    }
    this.updateStats();
    this.notifyDataChanged();
  }

  // -------------------------------------------------------------------
  // 이상적인 한국형 신도시 템플릿 로드 (판교/광교 모델)
  // -------------------------------------------------------------------
  loadIdealKoreanNewTownPreset() {
    this.nodes = [];
    this.roads = [];
    this.zoneCells.clear();
    this.zoneBlocks = [];
    this.roundabouts = [];
    this.cars = [];
    this.simulationTime = 0;
    this.brtTimer = 0;

    if (typeof getIdealKoreanNewTownPresetData === 'function') {
      const data = getIdealKoreanNewTownPresetData();
      this.nodes = data.nodes;
      this.roads = data.roads;
      this.zoneBlocks = data.zoneBlocks || [];
      this.roundabouts = data.roundabouts || [];
      this.nextNodeId = Math.max(...data.nodes.map(n => n.id)) + 1;
      this.nextRoadId = Math.max(...data.roads.map(r => r.id)) + 1;

      // 구역 블록 셀 변환 (landUse 메타데이터 보존)
      if (data.zoneBlocks) {
        for (const b of data.zoneBlocks) {
          this.fillZoneBlock(b.x, b.y, b.w, b.h, b.type, b.landUse, b.name);
        }
      }

      // 도로변 그리드 생성
      for (const r of this.roads) {
        this.generateZoningGridForRoad(r);
      }

      this.camera = { x: 1200, y: 900, zoom: 0.52 };
    } else {
      console.warn('getIdealKoreanNewTownPresetData not found, using fallback');
    }

    this.updateStats();
    this.notifyDataChanged();
  }

  fillZoneBlock(x0, y0, w, h, type, landUse = null, name = '') {
    const cellSize = 16;
    for (let x = x0; x < x0 + w; x += cellSize) {
      for (let y = y0; y < y0 + h; y += cellSize) {
        this.zoneCells.set(`${x},${y}`, { x, y, type, landUse, name });
      }
    }
  }

  // -------------------------------------------------------------------
  // 실시간 교통 시뮬레이션 루프
  // -------------------------------------------------------------------
  updateSimulation(dt) {
    // 1. WASD 키보드 뷰포트 이동
    const panSpeed = (350 * (dt / 1000)) / this.camera.zoom;
    if (this.keys['w'] || this.keys['arrowup']) this.camera.y -= panSpeed;
    if (this.keys['s'] || this.keys['arrowdown']) this.camera.y += panSpeed;
    if (this.keys['a'] || this.keys['arrowleft']) this.camera.x -= panSpeed;
    if (this.keys['d'] || this.keys['arrowright']) this.camera.x += panSpeed;

    if (!this.isPlaying) return;

    const elapsed = dt / 1000 * this.simSpeed;
    this.simulationTime = (this.simulationTime || 0) + elapsed;
    this.brtTimer = (this.brtTimer || 0) + elapsed;
    if (this.brtTimer >= 20) {
      this.brtTimer %= 20;
      this.spawnBrtBus();
    }

    // 2. 차량 스폰
    if (Math.random() < 0.12 * this.simSpeed && this.roads.length > 0) {
      this.spawnCar();
    }

    // 3. 도로 통행량 감쇠
    for (const r of this.roads) {
      r.trafficLoad *= 0.988;
      r.recentCars = (r.recentCars || 0) * 0.992;
    }

    // 4. 차량 이동
    const finished = [];
    for (let i = 0; i < this.cars.length; i++) {
      const car = this.cars[i];
      const road = this.roads[car.roadIndex];
      if (!road || road.length <= 0) {
        finished.push(i);
        continue;
      }

      if (car.dwell > 0) { car.dwell -= elapsed; continue; }

      const cfg = ROAD_CONFIGS[road.type] || ROAD_CONFIGS.local;
      const speedCoeff = Math.max(0.18, 1.0 - (road.trafficLoad / cfg.capacity));
      const moveDist = ((road.speedLimit || cfg.maxSpeed) * speedCoeff * (dt / 1000) * 7.5) * this.simSpeed;

      const oldProgress = car.progress;
      car.progress += moveDist;
      if (car.kind === 'bus' && road.facility === 'brt' && car.stoppedRoad !== road.id &&
          oldProgress < road.length / 2 && car.progress >= road.length / 2) {
        car.progress = road.length / 2;
        car.stoppedRoad = road.id;
        car.dwell = 5;
      }
      road.trafficLoad += 0.02 * this.simSpeed;
      road.recentCars = (road.recentCars || 0) + 0.01;

      let current = road;
      while (current.length > 0 && car.progress >= current.length) {
        if (car.path && car.path.length && !this.signalIsGreen(current)) {
          car.progress = Math.max(0, current.length - 2);
          break;
        }
        car.progress -= current.length;
        if (!car.path || car.path.length === 0) { finished.push(i); break; }
        car.roadIndex = car.path.shift();
        current = this.roads[car.roadIndex];
        if (!current || current.length <= 0) { finished.push(i); break; }
      }
    }

    for (let j = finished.length - 1; j >= 0; j--) {
      this.cars.splice(finished[j], 1);
    }

    document.getElementById('car-count').textContent = this.cars.length;
    this.updateTrafficMeter();
  }

  signalIsGreen(road) {
    const from = this.nodes.find(node => node.id === road.from);
    const to = this.nodes.find(node => node.id === road.to);
    if (!from || !to || !to.signal) return true;
    const signal = to.signal;
    const northSouth = Math.abs(to.y - from.y) >= Math.abs(to.x - from.x);
    const phase = (this.simulationTime || 0) % signal.cycle;
    return northSouth ? phase < signal.northSouthGreen : phase >= signal.northSouthGreen;
  }

  spawnBrtBus() {
    const segments = this.roads.map((road, idx) => ({ road, idx })).filter(item => item.road.facility === 'brt');
    const start = segments.find(item => !segments.some(other => other.road.to === item.road.from));
    if (!start) return;
    const path = [];
    let current = start;
    const visited = new Set([current.idx]);
    while (current) {
      const next = segments.find(item => item.road.from === current.road.to && !visited.has(item.idx));
      if (!next) break;
      path.push(next.idx); visited.add(next.idx); current = next;
    }
    this.cars.push({ id: Math.random(), kind: 'bus', roadIndex: start.idx, progress: 0, color: '#e74c3c', path });
  }

  spawnCar() {
    if (this.roads.length === 0) return;
    const driveable = this.roads.map((r, idx) => ({ r, idx }))
      .filter(({ r }) => r.type !== 'parkway' && r.length > 0);
    if (!driveable.length) return;
    const rIdx = driveable[Math.floor(Math.random() * driveable.length)].idx;
    const startRoad = this.roads[rIdx];

    const path = [];
    const visited = new Set([rIdx]);
    let currNode = startRoad.to;
    for (let s = 0; s < 24; s++) {
      const nextCandidates = driveable.filter(item => item.r.from === currNode && !visited.has(item.idx));
      if (nextCandidates.length === 0) break;
      const chosen = nextCandidates[Math.floor(Math.random() * nextCandidates.length)];
      path.push(chosen.idx);
      visited.add(chosen.idx);
      currNode = chosen.r.to;
    }

    this.cars.push({
      id: Math.random(),
      roadIndex: rIdx,
      progress: 0,
      color: Math.random() > 0.5 ? '#58a6ff' : '#f0883e',
      path
    });
  }

  updateTrafficMeter() {
    let smooth = 0, slow = 0, congested = 0;
    let worst = null;
    let maxCongestion = 0;

    for (const r of this.roads) {
      const cfg = ROAD_CONFIGS[r.type] || ROAD_CONFIGS.local;
      const ratio = r.trafficLoad / cfg.capacity;
      if (ratio < 0.35) smooth++;
      else if (ratio < 0.70) slow++;
      else {
        congested++;
        if (ratio > maxCongestion) {
          maxCongestion = ratio;
          worst = r;
        }
      }
    }

    const total = Math.max(1, this.roads.length);
    const pSmooth = Math.round((smooth / total) * 100);
    const pSlow = Math.round((slow / total) * 100);
    const pCongested = Math.round((congested / total) * 100);

    document.getElementById('traffic-smooth').style.width = `${pSmooth}%`;
    document.getElementById('traffic-slow').style.width = `${pSlow}%`;
    document.getElementById('traffic-congested').style.width = `${pCongested}%`;
    document.getElementById('val-smooth').textContent = `${pSmooth}%`;
    document.getElementById('val-slow').textContent = `${pSlow}%`;
    document.getElementById('val-congested').textContent = `${pCongested}%`;

    const alertBox = document.getElementById('bottleneck-alert');
    if (worst && maxCongestion > 0.75) {
      alertBox.style.display = 'block';
      const cfg = ROAD_CONFIGS[worst.type];
      document.getElementById('bottleneck-text').textContent =
        `[${cfg.name} (${worst.lanes}차선)] 구간 병목 심각! 차선 확장이 필요합니다.`;
    } else {
      alertBox.style.display = 'none';
    }
  }

  updateStats() {
    let pop = 0, jobs = 0;
    for (const cell of this.zoneCells.values()) {
      if (cell.type && ZONE_CONFIGS[cell.type]) {
        pop += ZONE_CONFIGS[cell.type].pop;
        jobs += ZONE_CONFIGS[cell.type].jobs;
      }
    }

    let roadLen = 0;
    for (const r of this.roads) roadLen += r.length;

    document.getElementById('stat-population').textContent = `${pop.toLocaleString()} 명`;
    document.getElementById('stat-jobs').textContent = `${jobs.toLocaleString()} 개`;
    document.getElementById('stat-roads').textContent = `${(roadLen / 1000).toFixed(1)} km`;
  }

  updateInspector() {
    const emptyDiv = document.getElementById('inspector-empty');
    const contentDiv = document.getElementById('inspector-content');

    if (!this.selectedRoad) {
      emptyDiv.style.display = 'block';
      contentDiv.style.display = 'none';
      return;
    }

    emptyDiv.style.display = 'none';
    contentDiv.style.display = 'block';

    const r = this.selectedRoad;
    const cfg = ROAD_CONFIGS[r.type] || ROAD_CONFIGS.local;
    document.getElementById('insp-type').textContent = cfg.name;
    document.getElementById('insp-lanes').textContent = `${r.lanes} 차선`;
    document.getElementById('insp-length').textContent = `${Math.round(r.length)} m`;
    document.getElementById('insp-flow').textContent = `${Math.round(r.recentCars * 18)} 대/시간`;
  }

  clearAll() {
    if (confirm('모든 도로와 구역을 초기화하시겠습니까?')) {
      this.nodes = [];
      this.roads = [];
      this.zoneCells.clear();
      this.zoneBlocks = [];
      this.roundabouts = [];
      this.cars = [];
      this.selectedRoad = null;
      this.resetDrawingState();
      this.updateStats();
      this.updateInspector();
      this.notifyDataChanged();
    }
  }

  // -------------------------------------------------------------------
  // 60 FPS 캔버스 렌더러
  // -------------------------------------------------------------------
  loop() {
    const now = performance.now();
    const dt = Math.min(now - this.lastFrameTime, 100);
    this.lastFrameTime = now;

    this.updateSimulation(dt);
    if (this.viewMode === '3d' && this.view3D) {
      this.view3D.render(dt);
    } else {
      this.render();
    }
    requestAnimationFrame(() => this.loop());
  }

  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    this.renderGrid();
    this.renderZoningGrid();
    this.renderBuildings(); // 2.5D 입체 건물 (아파트/상가/테크노밸리/수변)
    this.renderRoads();     // 고화질 실제 도로 (BRT 전용차로, 차선 디바이더)
    this.renderCrosswalks(); // 교차로 횡단보도
    this.renderCars();      // 방향성 미니 차량 & BRT 버스
    this.renderIntersections();
    this.renderPreview();
  }

  renderGrid() {
    const ctx = this.ctx;
    const zoom = this.camera.zoom;
    const gridSize = 100 * zoom;

    const startX = ((this.canvas.width / 2 - this.camera.x * zoom) % gridSize + gridSize) % gridSize;
    const startY = ((this.canvas.height / 2 - this.camera.y * zoom) % gridSize + gridSize) % gridSize;

    ctx.strokeStyle = '#141a24';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = startX; x < this.canvas.width; x += gridSize) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.canvas.height);
    }
    for (let y = startY; y < this.canvas.height; y += gridSize) {
      ctx.moveTo(0, y);
      ctx.lineTo(this.canvas.width, y);
    }
    ctx.stroke();
  }

  renderZoningGrid() {
    const ctx = this.ctx;
    const zoom = this.camera.zoom;
    const cellSize = 16 * zoom;
    if (cellSize < 3) return; // 너무 작으면 그리지 않음

    // 구역별로 묶어서 한번에 fillRect (배치 렌더링 - 60fps 보장)
    const batches = {};
    for (const type of Object.keys(ZONE_CONFIGS)) {
      batches[type] = [];
    }
    const emptyCells = [];

    for (const cell of this.zoneCells.values()) {
      const p = this.worldToScreen(cell.x, cell.y);
      if (p.x < -cellSize || p.x > this.canvas.width || p.y < -cellSize || p.y > this.canvas.height) continue;

      if (cell.type && batches[cell.type]) {
        batches[cell.type].push(p);
      } else if (this.currentCategory === 'zones' && zoom > 0.6) {
        emptyCells.push(p);
      }
    }

    for (const [type, pts] of Object.entries(batches)) {
      if (pts.length === 0) continue;
      const cfg = ZONE_CONFIGS[type];
      ctx.fillStyle = cfg.fill;
      for (const p of pts) {
        ctx.fillRect(p.x, p.y, cellSize - 0.5, cellSize - 0.5);
      }
    }

    if (emptyCells.length > 0) {
      ctx.strokeStyle = 'rgba(88, 166, 255, 0.2)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (const p of emptyCells) {
        ctx.rect(p.x, p.y, cellSize - 0.5, cellSize - 0.5);
      }
      ctx.stroke();
    }
  }

  // ===================================================================
  // [비주얼 대개편] 고화질 실제 도로 렌더러 (BRT 전용차로, 연석, 중앙선)
  // ===================================================================
  renderRoads() {
    const ctx = this.ctx;
    const zoom = this.camera.zoom;

    // 고도 및 입체교차 순 정렬 (지상도로 -> 고가 램프 -> 플라이오버 최상층)
    const sortedRoads = [...this.roads].sort((a, b) => {
      const aF = this.nodes.find(n => n.id === a.from);
      const aT = this.nodes.find(n => n.id === a.to);
      const bF = this.nodes.find(n => n.id === b.from);
      const bT = this.nodes.find(n => n.id === b.to);
      const aElev = Math.max(aF?.z || 0, aT?.z || 0) + (a.facility === 'flyover' ? 10 : (a.gradeSeparated ? 4 : 0));
      const bElev = Math.max(bF?.z || 0, bT?.z || 0) + (b.facility === 'flyover' ? 10 : (b.gradeSeparated ? 4 : 0));
      return aElev - bElev;
    });

    for (const r of sortedRoads) {
      const fNode = this.nodes.find(n => n.id === r.from);
      const tNode = this.nodes.find(n => n.id === r.to);
      if (!fNode || !tNode) continue;

      const p1 = this.worldToScreen(fNode.x, fNode.y);
      const p2 = this.worldToScreen(tNode.x, tNode.y);
      const cfg = ROAD_CONFIGS[r.type] || ROAD_CONFIGS.local;
      const roadW = (cfg.width + (r.lanes - cfg.lanes) * 3) * zoom;

      const isElevated = ((fNode.z || 0) > 1 || (tNode.z || 0) > 1 || r.gradeSeparated || r.bridge);
      const isBulldozeHover = (this.currentCategory === 'bulldoze' && this.hoveredRoad === r);
      const isSelected = (this.selectedRoad === r);

      // 입체교차로 및 고가도로 그림자 효과
      if (isElevated) {
        ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
        ctx.shadowBlur = 8 * zoom;
        ctx.shadowOffsetY = 4 * zoom;
      }

      // 1. 도로변 보도블록 & 연석 (Sidewalk Curb)
      ctx.strokeStyle = isBulldozeHover ? '#ff4d4f' : (isSelected ? '#58a6ff' : (isElevated ? '#8b949e' : '#6b7280'));
      ctx.lineWidth = Math.max(roadW + (isElevated ? 6 : 5) * zoom, 6);
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      if (r.midPoint) {
        const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
        ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
      } else {
        ctx.lineTo(p2.x, p2.y);
      }
      ctx.stroke();

      // 그림자 리셋
      if (isElevated) {
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;
      }

      // 2. 실제 아스팔트 노면 본선 (Dark Asphalt)
      ctx.strokeStyle = isBulldozeHover ? '#ff7875' : '#1f242d';
      ctx.lineWidth = Math.max(roadW, 3);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      if (r.midPoint) {
        const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
        ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
      } else {
        ctx.lineTo(p2.x, p2.y);
      }
      ctx.stroke();

      if (roadW < 7) continue;

      // 3. 도로 유형별 정밀 차선 디테일
      if (r.type === 'highway' && r.facility !== 'expressway') {
        // [주간선 8차선 BRT]: 중앙 붉은색 버스전용차로 유색 포장 노면
        ctx.strokeStyle = 'rgba(215, 38, 56, 0.9)';
        ctx.lineWidth = Math.max(roadW * 0.28, 4);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        if (r.midPoint) {
          const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
          ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
        } else {
          ctx.lineTo(p2.x, p2.y);
        }
        ctx.stroke();

        // 파란색 BRT 전용차선 구분선
        ctx.strokeStyle = '#388bfd';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        if (r.midPoint) {
          const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
          ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
        } else {
          ctx.lineTo(p2.x, p2.y);
        }
        ctx.stroke();

        // 일반차선 흰색 점선들
        ctx.strokeStyle = '#ffffff77';
        ctx.lineWidth = 1;
        ctx.setLineDash([8, 8]);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        if (r.midPoint) {
          const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
          ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
        } else {
          ctx.lineTo(p2.x, p2.y);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      } else if (r.type === 'arterial') {
        // [보조간선 4차선]: 노란색 이중 중앙선 + 흰색 점선
        ctx.strokeStyle = '#f1c40f';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        if (r.midPoint) {
          const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
          ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
        } else {
          ctx.lineTo(p2.x, p2.y);
        }
        ctx.stroke();

        // 차선 점선
        ctx.strokeStyle = '#ffffff66';
        ctx.lineWidth = 1;
        ctx.setLineDash([6, 6]);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        if (r.midPoint) {
          const mp = this.worldToScreen(r.midPoint.x, r.midPoint.y);
          ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
        } else {
          ctx.lineTo(p2.x, p2.y);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      } else if (r.type === 'local') {
        // [생활도로 2차선]: 중앙 노란색 점선
        ctx.strokeStyle = '#f1c40f88';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
        ctx.setLineDash([]);
      } else if (r.type === 'parkway') {
        // [선형 보행녹지축]: 우레탄 에메랄드 산책로 트랙
        ctx.strokeStyle = '#27ae60';
        ctx.lineWidth = Math.max(roadW * 0.7, 3);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }

      // 교통 체증 히트맵 오버레이 (정체 시 반투명 붉은 안개)
      const ratio = r.trafficLoad / cfg.capacity;
      if (ratio > 0.4) {
        ctx.strokeStyle = ratio > 0.75 ? 'rgba(248, 81, 73, 0.45)' : 'rgba(210, 153, 34, 0.35)';
        ctx.lineWidth = roadW + 8 * zoom;
        ctx.stroke();
      }
    }

    // 회전교차로 (Roundabout) 중앙 교통섬 및 2D 랜드스케이프 장식
    if (this.roundabouts && this.roundabouts.length > 0) {
      for (const rb of this.roundabouts) {
        const p = this.worldToScreen(rb.x, rb.y);
        const rScreen = rb.radius * zoom;
        const islandR = rScreen * 0.62;

        if (islandR > 3) {
          // 1. 중앙 교통섬 잔디밭
          ctx.fillStyle = '#27ae60';
          ctx.beginPath();
          ctx.arc(p.x, p.y, islandR, 0, Math.PI * 2);
          ctx.fill();

          // 2. 외곽 화강석 연석 경계
          ctx.strokeStyle = '#dfe6e9';
          ctx.lineWidth = Math.max(2.5 * zoom, 1.5);
          ctx.stroke();

          // 3. 중앙 조경 소나무 및 화단
          if (islandR > 7) {
            ctx.fillStyle = '#1e824c';
            ctx.beginPath();
            ctx.arc(p.x, p.y, islandR * 0.45, 0, Math.PI * 2);
            ctx.fill();

            // 화단 테두리
            ctx.strokeStyle = '#f1c40f88';
            ctx.lineWidth = 1;
            ctx.stroke();
          }

          // 4. 로터리 라벨
          if (zoom > 0.45) {
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold ${Math.max(9 * zoom, 8)}px sans-serif`;
            ctx.textAlign = 'center';
            ctx.fillText(rb.name, p.x, p.y + islandR + 12 * zoom);
            ctx.textAlign = 'start';
          }
        }
      }
    }
  }

  // ===================================================================
  // [비주얼 대개편] 교차로 횡단보도 (Zebra Crossings)
  // ===================================================================
  renderCrosswalks() {
    if (this.camera.zoom < 0.45) return;
    const ctx = this.ctx;
    const zoom = this.camera.zoom;

    for (const r of this.roads) {
      if (r.type === 'parkway') continue;
      const fNode = this.nodes.find(n => n.id === r.from);
      const tNode = this.nodes.find(n => n.id === r.to);
      if (!fNode || !tNode) continue;

      const dx = tNode.x - fNode.x;
      const dy = tNode.y - fNode.y;
      const len = Math.hypot(dx, dy);
      if (len < 60) continue;

      const ux = dx / len;
      const uy = dy / len;
      const nx = -uy;
      const ny = ux;
      const cfg = ROAD_CONFIGS[r.type];
      const roadW = cfg.width;

      // 양쪽 끝 교차로 진입부에 횡단보도 줄무늬 렌더링
      for (const distFromEnd of [14, len - 14]) {
        const cx = fNode.x + ux * distFromEnd;
        const cy = fNode.y + uy * distFromEnd;
        const cp = this.worldToScreen(cx, cy);

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 2.2 * zoom;

        const stripes = Math.floor(roadW / 3.5);
        for (let s = -stripes / 2; s <= stripes / 2; s++) {
          const sx = cx + nx * (s * 3.2);
          const sy = cy + ny * (s * 3.2);
          const pStart = this.worldToScreen(sx - ux * 2.5, sy - uy * 2.5);
          const pEnd = this.worldToScreen(sx + ux * 2.5, sy + uy * 2.5);
          ctx.beginPath();
          ctx.moveTo(pStart.x, pStart.y);
          ctx.lineTo(pEnd.x, pEnd.y);
          ctx.stroke();
        }
      }
    }
  }

  // ===================================================================
  // [비주얼 대개편] 실제 건물 2.5D 입체 렌더러 (아파트, 쇼핑몰, 지식산업센터, 학교·운동장, 환승센터, 수변)
  // ===================================================================
  renderBuildings() {
    const ctx = this.ctx;
    const zoom = this.camera.zoom;

    // 0. 특수 랜드마크 부지 정밀 렌더링 (학교와 운동장, 복합환승센터, 하천 축)
    if (this.zoneBlocks && this.zoneBlocks.length > 0) {
      for (const b of this.zoneBlocks) {
        const p = this.worldToScreen(b.x, b.y);
        const bW = b.w * zoom;
        const bH = b.h * zoom;

        // [A] 초등학교와 운동장 (초품아)
        if (b.landUse === 'school') {
          // 1) 서측 교사동 본관
          const schW = 76 * zoom;
          const schH = 28 * zoom;
          const height3D = 24 * zoom;

          // 교사동 그림자
          ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
          ctx.fillRect(p.x + 8 * zoom, p.y + 12 * zoom, schW, schH);

          // 본관 건물 벽면
          ctx.fillStyle = '#dfe6e9';
          ctx.fillRect(p.x + 4 * zoom, p.y + 12 * zoom - height3D, schW, schH);
          ctx.strokeStyle = '#2d3436';
          ctx.lineWidth = 1;
          ctx.strokeRect(p.x + 4 * zoom, p.y + 12 * zoom - height3D, schW, schH);

          // 옥상 장식
          ctx.fillStyle = '#0984e3';
          ctx.fillRect(p.x + 28 * zoom, p.y + 8 * zoom - height3D, 24 * zoom, 6 * zoom);

          // 교사동 창문
          if (zoom > 0.4) {
            ctx.fillStyle = '#2d3436';
            for (let wx = p.x + 10 * zoom; wx < p.x + schW - 8 * zoom; wx += 8 * zoom) {
              ctx.fillRect(wx, p.y + 16 * zoom - height3D, 5 * zoom, 6 * zoom);
              ctx.fillRect(wx, p.y + 26 * zoom - height3D, 5 * zoom, 6 * zoom);
            }
          }

          // 2) 동측 운동장 (붉은 우레탄 트랙 + 에메랄드 잔디구장 + 축구 골대)
          const trkX = p.x + 88 * zoom;
          const trkY = p.y + 16 * zoom;
          const trkW = 96 * zoom;
          const trkH = 76 * zoom;

          // 붉은색 우레탄 육상 트랙
          ctx.fillStyle = '#c0392b';
          ctx.beginPath();
          if (typeof ctx.roundRect === 'function') {
            ctx.roundRect(trkX, trkY, trkW, trkH, 18 * zoom);
          } else {
            ctx.rect(trkX, trkY, trkW, trkH);
          }
          ctx.fill();
          ctx.strokeStyle = '#e74c3c';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          // 흰색 달리기 라인
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.65)';
          ctx.lineWidth = 1;
          ctx.stroke();

          // 내부 잔디 축구장
          const pitchInset = 9 * zoom;
          ctx.fillStyle = '#27ae60';
          ctx.fillRect(trkX + pitchInset, trkY + pitchInset, trkW - pitchInset * 2, trkH - pitchInset * 2);
          ctx.strokeStyle = '#ffffff88';
          ctx.lineWidth = 1;
          ctx.strokeRect(trkX + pitchInset, trkY + pitchInset, trkW - pitchInset * 2, trkH - pitchInset * 2);

          // 하프라인 & 센터 서클
          ctx.beginPath();
          ctx.moveTo(trkX + trkW * 0.5, trkY + pitchInset);
          ctx.lineTo(trkX + trkW * 0.5, trkY + trkH - pitchInset);
          ctx.arc(trkX + trkW * 0.5, trkY + trkH * 0.5, 7 * zoom, 0, Math.PI * 2);
          ctx.stroke();

          // 명칭 라벨
          if (zoom > 0.42) {
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold ${Math.max(10 * zoom, 9)}px sans-serif`;
            ctx.fillText(`🏫 ${b.schoolName || '초등학교 & 운동장'}`, p.x + 8 * zoom, p.y + bH - 8 * zoom);
          }
        }

        // [B] 대형 복합환승센터
        else if (b.landUse === 'transit') {
          ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
          ctx.fillRect(p.x + 8 * zoom, p.y + 8 * zoom, bW, bH);

          // 실버 유선형 아치 지붕 캐노피
          const grad = ctx.createLinearGradient(p.x, p.y, p.x + bW, p.y + bH);
          grad.addColorStop(0, '#74b9ff');
          grad.addColorStop(0.5, '#dfe6e9');
          grad.addColorStop(1, '#0984e3');
          ctx.fillStyle = grad;
          ctx.beginPath();
          if (typeof ctx.roundRect === 'function') {
            ctx.roundRect(p.x, p.y, bW, bH, 12 * zoom);
          } else {
            ctx.rect(p.x, p.y, bW, bH);
          }
          ctx.fill();
          ctx.strokeStyle = '#0984e3';
          ctx.lineWidth = 2;
          ctx.stroke();

          if (zoom > 0.42) {
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold ${Math.max(11 * zoom, 9)}px sans-serif`;
            ctx.fillText('🚊 복합환승센터', p.x + 10 * zoom, p.y + 24 * zoom);
            ctx.font = `${Math.max(9 * zoom, 8)}px sans-serif`;
            ctx.fillText('KTX·광역버스·환승터미널', p.x + 10 * zoom, p.y + 40 * zoom);
          }
        }

        // [C] 구분 가능한 하천 축
        else if (b.landUse === 'river') {
          // 깊은 푸른 수면
          const rGrad = ctx.createLinearGradient(p.x, p.y, p.x, p.y + bH);
          rGrad.addColorStop(0, '#0984e3');
          rGrad.addColorStop(0.5, '#1b6ca8');
          rGrad.addColorStop(1, '#0984e3');
          ctx.fillStyle = rGrad;
          ctx.fillRect(p.x, p.y + 16 * zoom, bW, bH - 32 * zoom);

          // 수변 석축 제방
          ctx.strokeStyle = '#636e72';
          ctx.lineWidth = 2 * zoom;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y + 16 * zoom);
          ctx.lineTo(p.x + bW, p.y + 16 * zoom);
          ctx.moveTo(p.x, p.y + bH - 16 * zoom);
          ctx.lineTo(p.x + bW, p.y + bH - 16 * zoom);
          ctx.stroke();

          // 수변 산책로
          ctx.fillStyle = '#ffeaa766';
          ctx.fillRect(p.x, p.y + 8 * zoom, bW, 7 * zoom);
          ctx.fillRect(p.x, p.y + bH - 15 * zoom, bW, 7 * zoom);
        }
      }
    }

    if (this.zoneCells.size === 0) return;

    // 방문한 셀 체크를 위한 Set
    const visited = new Set();
    const cellSize = 16;

    for (const cell of this.zoneCells.values()) {
      const cellKey = cell.x + ',' + cell.y;
      if (!cell.type || visited.has(cellKey)) continue;

      // 특수 랜드마크 부지는 위에서 전용 그래픽으로 렌더링했으므로 중복 렌더 방지
      if (cell.landUse === 'school' || cell.landUse === 'transit' || cell.landUse === 'river') continue;

      const type = cell.type;
      const p = this.worldToScreen(cell.x, cell.y);
      if (p.x < -100 || p.x > this.canvas.width + 100 || p.y < -100 || p.y > this.canvas.height + 100) continue;

      // 1. 한국형 판상형/타워형 아파트 단지 (Residential)
      if (type === 'residential') {
        // 48m x 20m 크기의 아파트 동(Building Block)으로 렌더링
        if ((cell.x % 64 === 0) && (cell.y % 48 === 0)) {
          const bW = 54 * zoom;
          const bH = 22 * zoom;
          const height3D = 28 * zoom; // 2.5D 돌출 높이

          // 그림자
          ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
          ctx.fillRect(p.x + 8 * zoom, p.y + 8 * zoom, bW, bH);

          // 건물 측면 (입체감)
          ctx.fillStyle = '#8395a7';
          ctx.beginPath();
          ctx.moveTo(p.x, p.y + bH);
          ctx.lineTo(p.x, p.y + bH - height3D);
          ctx.lineTo(p.x + bW, p.y + bH - height3D);
          ctx.lineTo(p.x + bW, p.y + bH);
          ctx.fill();

          // 건물 정면/외벽 (밝은 크림색)
          ctx.fillStyle = '#c8d6e5';
          ctx.fillRect(p.x, p.y - height3D, bW, bH);
          ctx.strokeStyle = '#576574';
          ctx.lineWidth = 1;
          ctx.strokeRect(p.x, p.y - height3D, bW, bH);

          // 발코니 창문 패턴 (격자)
          if (zoom > 0.5) {
            ctx.fillStyle = '#222f3e';
            for (let wx = p.x + 4 * zoom; wx < p.x + bW - 4 * zoom; wx += 7 * zoom) {
              for (let wy = p.y - height3D + 3 * zoom; wy < p.y - height3D + bH - 3 * zoom; wy += 5 * zoom) {
                ctx.fillRect(wx, wy, 4 * zoom, 2.5 * zoom);
              }
            }

            // 옥상 헬리패드 & 물탱크실
            ctx.fillStyle = '#576574';
            ctx.fillRect(p.x + bW / 2 - 6 * zoom, p.y - height3D - 4 * zoom, 12 * zoom, 6 * zoom);
            ctx.fillStyle = '#ffffff';
            ctx.font = Math.max(7 * zoom, 6) + 'px sans-serif';
            ctx.fillText('H', p.x + bW / 2 - 3 * zoom, p.y - height3D + 2 * zoom);
          }

          // 단지 내 조경수 (초록색 가로수)
          ctx.fillStyle = '#10ac84';
          ctx.beginPath();
          ctx.arc(p.x - 8 * zoom, p.y + 10 * zoom, 5 * zoom, 0, Math.PI * 2);
          ctx.arc(p.x + bW + 8 * zoom, p.y + 10 * zoom, 6 * zoom, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      // 2. 중심상업 글래스 타워 & 쇼핑몰 (Commercial)
      else if (type === 'commercial') {
        if ((cell.x % 48 === 0) && (cell.y % 48 === 0)) {
          const bW = 40 * zoom;
          const bH = 36 * zoom;
          const height3D = 38 * zoom;

          // 그림자
          ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
          ctx.fillRect(p.x + 6 * zoom, p.y + 6 * zoom, bW, bH);

          // 블루 틴티드 글래스 파사드 (유리 커튼월)
          ctx.fillStyle = '#2e86de';
          ctx.fillRect(p.x, p.y - height3D, bW, bH);
          ctx.strokeStyle = '#54a0ff';
          ctx.lineWidth = 1.2;
          ctx.strokeRect(p.x, p.y - height3D, bW, bH);

          // 옥상 루프탑 가든 & 팬 유닛
          if (zoom > 0.5) {
            ctx.fillStyle = '#1dd1a1';
            ctx.fillRect(p.x + 4 * zoom, p.y - height3D + 4 * zoom, bW - 8 * zoom, bH - 8 * zoom);
            ctx.fillStyle = '#c8d6e5';
            ctx.fillRect(p.x + 10 * zoom, p.y - height3D + 10 * zoom, 8 * zoom, 8 * zoom);
          }
        }
      }
      // 3. 테크노밸리 첨단 지식산업센터 (Industrial / R&D)
      else if (type === 'industrial') {
        if ((cell.x % 64 === 0) && (cell.y % 48 === 0)) {
          const bW = 50 * zoom;
          const bH = 32 * zoom;
          const height3D = 22 * zoom;

          ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
          ctx.fillRect(p.x + 6 * zoom, p.y + 6 * zoom, bW, bH);

          // 모던 지식산업센터 큐브 외벽
          ctx.fillStyle = '#5f27cd';
          ctx.fillRect(p.x, p.y - height3D, bW, bH);
          ctx.strokeStyle = '#9b59b6';
          ctx.lineWidth = 1;
          ctx.strokeRect(p.x, p.y - height3D, bW, bH);

          // 옥상 솔라 패널 (태양광 집열판)
          if (zoom > 0.5) {
            ctx.fillStyle = '#341f97';
            ctx.fillRect(p.x + 4 * zoom, p.y - height3D + 4 * zoom, bW - 8 * zoom, bH - 8 * zoom);
            ctx.strokeStyle = '#00d2d3';
            ctx.lineWidth = 0.8;
            ctx.strokeRect(p.x + 4 * zoom, p.y - height3D + 4 * zoom, bW - 8 * zoom, bH - 8 * zoom);
          }
        }
      }
      // 4. 수변생태공원 및 하천 (Park)
      else if (type === 'park') {
        const cellSizeScreen = 16 * zoom;
        // 푸른 수변 잔디밭
        ctx.fillStyle = '#10ac8455';
        ctx.fillRect(p.x, p.y, cellSizeScreen, cellSizeScreen);

        // 하천 물결
        if ((cell.y >= 960 && cell.y <= 1080) || cell.y % 32 === 0) {
          ctx.fillStyle = '#00cec9';
          ctx.fillRect(p.x, p.y + cellSizeScreen * 0.25, cellSizeScreen, cellSizeScreen * 0.5);
        }

        // 공원 가로수 프랍
        if (cell.x % 32 === 0 && cell.y % 32 === 0 && zoom > 0.4) {
          ctx.fillStyle = '#01a3a4';
          ctx.beginPath();
          ctx.arc(p.x + cellSizeScreen / 2, p.y + cellSizeScreen / 2, 6 * zoom, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      visited.add(cellKey);
    }
  }

  // ===================================================================
  // [비주얼 대개편] 실제 미니 차량 & BRT 버스 & 전조등 렌더러
  // ===================================================================
  renderCars() {
    const ctx = this.ctx;
    const zoom = this.camera.zoom;

    for (const car of this.cars) {
      const road = this.roads[car.roadIndex];
      if (!road) continue;

      const fNode = this.nodes.find(n => n.id === road.from);
      const tNode = this.nodes.find(n => n.id === road.to);
      if (!fNode || !tNode) continue;

      const t = Math.min(1.0, car.progress / road.length);
      let wx, wy, angle;

      if (road.midPoint) {
        const mx = road.midPoint.x;
        const my = road.midPoint.y;
        wx = (1 - t)**2 * fNode.x + 2 * (1 - t) * t * mx + t**2 * tNode.x;
        wy = (1 - t)**2 * fNode.y + 2 * (1 - t) * t * my + t**2 * tNode.y;
        const dx = 2 * (1 - t) * (mx - fNode.x) + 2 * t * (tNode.x - mx);
        const dy = 2 * (1 - t) * (my - fNode.y) + 2 * t * (tNode.y - my);
        angle = Math.atan2(dy, dx);
      } else {
        wx = fNode.x + (tNode.x - fNode.x) * t;
        wy = fNode.y + (tNode.y - fNode.y) * t;
        angle = Math.atan2(tNode.y - fNode.y, tNode.x - fNode.x);
      }

      const p = this.worldToScreen(wx, wy);

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(angle);

      // 도로 유형이 BRT 고속도로일 경우 긴 빨간색 광역버스 (M-Bus)
      if (car.kind === 'bus') {
        const busL = Math.max(13 * zoom, 9);
        const busW = Math.max(5 * zoom, 3.5);

        // 버스 차체 (레드 M-Bus)
        ctx.fillStyle = '#e74c3c';
        ctx.fillRect(-busL / 2, -busW / 2, busL, busW);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 0.8;
        ctx.strokeRect(-busL / 2, -busW / 2, busL, busW);

        // 앞유리
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(busL / 2 - 3 * zoom, -busW / 2 + 0.5, 2.5 * zoom, busW - 1);

        // 헤드라이트 (노란 빛줄기)
        ctx.fillStyle = 'rgba(241, 196, 15, 0.4)';
        ctx.beginPath();
        ctx.moveTo(busL / 2, -busW / 2);
        ctx.lineTo(busL / 2 + 10 * zoom, -busW / 2 - 4 * zoom);
        ctx.lineTo(busL / 2 + 10 * zoom, busW / 2 + 4 * zoom);
        ctx.lineTo(busL / 2, busW / 2);
        ctx.fill();
      } else {
        // 일반 승용차 (세단)
        const carL = Math.max(7 * zoom, 5);
        const carW = Math.max(3.8 * zoom, 2.8);

        // 차체
        ctx.fillStyle = car.color || '#ecf0f1';
        ctx.fillRect(-carL / 2, -carW / 2, carL, carW);

        // 앞유리 / 뒷유리
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(carL / 2 - 2 * zoom, -carW / 2 + 0.5, 1.5 * zoom, carW - 1);
        ctx.fillRect(-carL / 2 + 0.8 * zoom, -carW / 2 + 0.5, 1.2 * zoom, carW - 1);

        // 후미등 (빨간 점)
        ctx.fillStyle = '#e74c3c';
        ctx.fillRect(-carL / 2, -carW / 2, 0.8 * zoom, 1 * zoom);
        ctx.fillRect(-carL / 2, carW / 2 - 1 * zoom, 0.8 * zoom, 1 * zoom);
      }

      ctx.restore();
    }
  }

  renderIntersections() {
    const ctx = this.ctx;
    for (const node of this.nodes) {
      const p = this.worldToScreen(node.x, node.y);
      const isHovered = (this.hoveredNode === node);
      const isDragged = (this.draggedNode === node);

      ctx.fillStyle = isDragged ? '#58a6ff' : (isHovered ? '#ffeb3b' : '#f0f6fc');
      ctx.beginPath();
      ctx.arc(p.x, p.y, Math.max((isHovered ? 6 : 4.5) * this.camera.zoom, 3.5), 0, Math.PI * 2);
      ctx.fill();
      if (node.signal) {
        const nsGreen = (this.simulationTime || 0) % node.signal.cycle < node.signal.northSouthGreen;
        ctx.fillStyle = nsGreen ? '#28c76f' : '#ff4d4f';
        ctx.fillRect(p.x - 2, p.y - 11, 4, 5);
        ctx.fillStyle = nsGreen ? '#ff4d4f' : '#28c76f';
        ctx.fillRect(p.x + 7, p.y - 2, 5, 4);
      }
    }
  }

  renderPreview() {
    const ctx = this.ctx;
    if (this.currentCategory !== 'roads' || !this.roadStartNode) return;

    const p1 = this.worldToScreen(this.roadStartNode.x, this.roadStartNode.y);
    const snapped = this.getSnappedPos(this.cursorWorld.x, this.cursorWorld.y, this.roadStartNode);
    const p2 = this.worldToScreen(snapped.x, snapped.y);

    ctx.strokeStyle = '#58a6ffcc';
    ctx.lineWidth = 4;
    ctx.setLineDash([8, 6]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);

    if (this.subMode === 'curve' && this.roadMidPoint) {
      const mp = this.worldToScreen(this.roadMidPoint.x, this.roadMidPoint.y);
      ctx.quadraticCurveTo(mp.x, mp.y, p2.x, p2.y);
    } else {
      ctx.lineTo(p2.x, p2.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // 스냅 타겟 지점 표시
    ctx.fillStyle = snapped.targetNode ? '#2ecc71' : (snapped.isRoadSplit ? '#f1c40f' : '#58a6ff');
    ctx.beginPath();
    ctx.arc(p2.x, p2.y, 6, 0, Math.PI * 2);
    ctx.fill();
  }

  // -------------------------------------------------------------------
  // CS2 JSON 내보내기
  // -------------------------------------------------------------------
  exportCS2() {
    const exportData = {
      version: "2.0-CS2",
      project: "서온해람시",
      createdAt: new Date().toISOString(),
      nodes: this.nodes.map(n => ({ id: n.id, x: n.x, y: n.y, z: n.z || 0 })),
      roads: this.roads.map(r => ({
        id: r.id,
        fromNode: r.from,
        toNode: r.to,
        type: r.type,
        lanes: r.lanes,
        speedLimit: r.speedLimit,
        lengthMeters: Math.round(r.length),
        midPoint: r.midPoint,
        facility: r.facility || null,
        bridge: !!r.bridge,
        gradeSeparated: !!r.gradeSeparated
      })),
      zones: Array.from(this.zoneCells.values()).filter(c => c.type),
      zoneBlocks: this.zoneBlocks || [],
      roundabouts: this.roundabouts || []
    };

    const jsonStr = JSON.stringify(exportData, null, 2);

    fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonStr
    })
    .then(r => r.json())
    .then(res => {
      if (res.status === 'success') {
        alert('CS2 설계 데이터가 성공적으로 저장되었습니다!\n위치: ' + res.path);
      } else {
        alert('저장 실패: ' + res.message);
      }
    })
    .catch(() => {
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'CS2_NewTown_Layout.json';
      a.click();
      URL.revokeObjectURL(url);
    });
  }
}

// 초기화
window.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('simCanvas');
  window.simulator = new CitySimulator(canvas);
  window.citySim = window.simulator;
});
