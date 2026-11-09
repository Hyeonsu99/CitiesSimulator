import os

code = r'''// =======================================================================
// K-City Planner : 3D 조감도 초고화질 렌더링 엔진 (view3d.js)
// 순수 WebGL 100% 오프라인 렌더러 (외부 라이브러리 및 CDN 의존성 전무)
// 한국형 신도시 조감도 레퍼런스 스타일 완벽 재현 (주거타워, 테크노밸리, 학교운동장, 환승센터, 산맥, 하천)
// 고품질 기준 구역: 중앙 BRT 주간선대로 및 수변 교차로·대형 아치 교량 정밀 구현
// =======================================================================

(function (global) {
  'use strict';

  // --- 4x4 행렬 연산 유틸리티 (순수 JS) ---
  const Mat4 = {
    create() {
      const out = new Float32Array(16);
      out[0] = 1; out[5] = 1; out[10] = 1; out[15] = 1;
      return out;
    },
    perspective(out, fovy, aspect, near, far) {
      const f = 1.0 / Math.tan(fovy / 2);
      const nf = 1 / (near - far);
      out[0] = f / aspect; out[1] = 0; out[2] = 0; out[3] = 0;
      out[4] = 0; out[5] = f; out[6] = 0; out[7] = 0;
      out[8] = 0; out[9] = 0; out[10] = (far + near) * nf; out[11] = -1;
      out[12] = 0; out[13] = 0; out[14] = (2 * far * near) * nf; out[15] = 0;
      return out;
    },
    lookAt(out, eye, center, up) {
      let x0, x1, x2, y0, y1, y2, z0, z1, z2, len;
      let eyex = eye[0], eyey = eye[1], eyez = eye[2];
      let centerx = center[0], centery = center[1], centerz = center[2];
      let upx = up[0], upy = up[1], upz = up[2];

      z0 = eyex - centerx;
      z1 = eyey - centery;
      z2 = eyez - centerz;
      len = 1 / Math.hypot(z0, z1, z2);
      z0 *= len; z1 *= len; z2 *= len;

      x0 = upy * z2 - upz * z1;
      x1 = upz * z0 - upx * z2;
      x2 = upx * z1 - upy * z0;
      len = Math.hypot(x0, x1, x2);
      if (!len) {
        x0 = 0; x1 = 0; x2 = 0;
      } else {
        len = 1 / len;
        x0 *= len; x1 *= len; x2 *= len;
      }

      y0 = z1 * x2 - z2 * x1;
      y1 = z2 * x0 - z0 * x2;
      y2 = z0 * x1 - z1 * x0;
      len = Math.hypot(y0, y1, y2);
      if (!len) {
        y0 = 0; y1 = 0; y2 = 0;
      } else {
        len = 1 / len;
        y0 *= len; y1 *= len; y2 *= len;
      }

      out[0] = x0; out[1] = y0; out[2] = z0; out[3] = 0;
      out[4] = x1; out[5] = y1; out[6] = z1; out[7] = 0;
      out[8] = x2; out[9] = y2; out[10] = z2; out[11] = 0;
      out[12] = -(x0 * eyex + x1 * eyey + x2 * eyez);
      out[13] = -(y0 * eyex + y1 * eyey + y2 * eyez);
      out[14] = -(z0 * eyex + z1 * eyey + z2 * eyez);
      out[15] = 1;
      return out;
    },
    multiply(out, a, b) {
      const a00 = a[0], a01 = a[1], a02 = a[2], a03 = a[3];
      const a10 = a[4], a11 = a[5], a12 = a[6], a13 = a[7];
      const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11];
      const a30 = a[12], a31 = a[13], a32 = a[14], a33 = a[15];

      let b0 = b[0], b1 = b[1], b2 = b[2], b3 = b[3];
      out[0] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[1] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[2] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[3] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;

      b0 = b[4]; b1 = b[5]; b2 = b[6]; b3 = b[7];
      out[4] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[5] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[6] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[7] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;

      b0 = b[8]; b1 = b[9]; b2 = b[10]; b3 = b[11];
      out[8] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[9] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[10] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[11] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;

      b0 = b[12]; b1 = b[13]; b2 = b[14]; b3 = b[15];
      out[12] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[13] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[14] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[15] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;
      return out;
    }
  };

  // --- 정밀 물리 기반 영감 셰이더 코드 (반구 앰비언트, 블린-퐁 스페큘러, AO) ---
  const VERTEX_SHADER_SRC = `
    attribute vec3 a_position;
    attribute vec3 a_normal;
    attribute vec4 a_color;

    uniform mat4 u_pvMatrix;

    varying vec3 v_normal;
    varying vec4 v_color;
    varying vec3 v_worldPos;

    void main() {
      v_worldPos = a_position;
      v_normal = a_normal;
      v_color = a_color;
      gl_Position = u_pvMatrix * vec4(a_position, 1.0);
    }
  `;

  const FRAGMENT_SHADER_SRC = `
    precision mediump float;

    varying vec3 v_normal;
    varying vec4 v_color;
    varying vec3 v_worldPos;

    uniform vec3 u_lightDir;
    uniform vec3 u_cameraPos;
    uniform vec3 u_fogColor;

    void main() {
      vec3 norm = normalize(v_normal);
      float diff = max(dot(norm, u_lightDir), 0.0);

      // 반구 앰비언트 조명 (하늘빛과 지면 반사광)
      vec3 skyLight = vec3(0.68, 0.78, 0.92);
      vec3 groundLight = vec3(0.32, 0.45, 0.28);
      vec3 ambient = mix(groundLight, skyLight, norm.z * 0.5 + 0.5) * 0.58;

      // 화사하고 맑은 태양광
      vec3 sunColor = vec3(1.10, 1.05, 0.96);
      vec3 light = ambient + sunColor * (diff * 0.65);

      // 높이 기반 앰비언트 오클루전(AO) 바닥 접지감 표현
      float ao = clamp(0.78 + 0.22 * (v_worldPos.z / 35.0), 0.70, 1.0);
      vec3 rgb = v_color.rgb * light * ao;

      // 유리창, 메탈릭 루프, 수면의 블린-퐁 스페큘러 및 프레넬 광택
      if (v_color.a > 1.05) {
        vec3 viewDir = normalize(u_cameraPos - v_worldPos);
        vec3 halfDir = normalize(u_lightDir + viewDir);
        float specPower = v_color.a > 1.30 ? 55.0 : 30.0;
        float spec = pow(max(dot(norm, halfDir), 0.0), specPower);
        float fresnel = pow(1.0 - max(dot(norm, viewDir), 0.0), 3.0);
        rgb += vec3(0.75, 0.85, 0.96) * (spec * 0.90 + fresnel * 0.35);
      }

      // 원경 대기 원근감 안개 (Atmospheric Aerial Fog)
      float dist = length(v_worldPos.xy - u_cameraPos.xy);
      float fogFactor = clamp((dist - 1500.0) / 3200.0, 0.0, 0.60);
      rgb = mix(rgb, u_fogColor, fogFactor);

      gl_FragColor = vec4(rgb, min(v_color.a, 1.0));
    }
  `;

  // --- 정밀 메쉬 빌더 클래스 ---
  class MeshData {
    constructor() {
      this.positions = [];
      this.normals = [];
      this.colors = [];
      this.indices = [];
      this.vertexCount = 0;
    }

    addVertex(x, y, z, nx, ny, nz, r, g, b, a = 1.0) {
      this.positions.push(x, y, z);
      this.normals.push(nx, ny, nz);
      this.colors.push(r, g, b, a);
      return this.vertexCount++;
    }

    addQuad(p1, p2, p3, p4, norm, color) {
      const nx = norm[0], ny = norm[1], nz = norm[2];
      const r = color[0], g = color[1], b = color[2], a = color[3] !== undefined ? color[3] : 1.0;
      const i1 = this.addVertex(p1[0], p1[1], p1[2], nx, ny, nz, r, g, b, a);
      const i2 = this.addVertex(p2[0], p2[1], p2[2], nx, ny, nz, r, g, b, a);
      const i3 = this.addVertex(p3[0], p3[1], p3[2], nx, ny, nz, r, g, b, a);
      const i4 = this.addVertex(p4[0], p4[1], p4[2], nx, ny, nz, r, g, b, a);
      this.indices.push(i1, i2, i3, i1, i3, i4);
    }

    addTriangle(p1, p2, p3, norm, color) {
      const nx = norm[0], ny = norm[1], nz = norm[2];
      const r = color[0], g = color[1], b = color[2], a = color[3] !== undefined ? color[3] : 1.0;
      const i1 = this.addVertex(p1[0], p1[1], p1[2], nx, ny, nz, r, g, b, a);
      const i2 = this.addVertex(p2[0], p2[1], p2[2], nx, ny, nz, r, g, b, a);
      const i3 = this.addVertex(p3[0], p3[1], p3[2], nx, ny, nz, r, g, b, a);
      this.indices.push(i1, i2, i3);
    }

    addBox(x, y, z, w, h, d, color, topColor = null) {
      const c = color;
      const tc = topColor || color;
      const x0 = x, x1 = x + w;
      const y0 = y, y1 = y + h;
      const z0 = z, z1 = z + d;

      // Top (+Z)
      this.addQuad([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [0, 0, 1], tc);
      // Bottom (-Z)
      this.addQuad([x0, y1, z0], [x1, y1, z0], [x1, y0, z0], [x0, y0, z0], [0, 0, -1], c);
      // Front (-Y)
      this.addQuad([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], [0, -1, 0], c);
      // Back (+Y)
      this.addQuad([x1, y1, z0], [x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [0, 1, 0], c);
      // Left (-X)
      this.addQuad([x0, y1, z0], [x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [-1, 0, 0], c);
      // Right (+X)
      this.addQuad([x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1], [1, 0, 0], c);
    }

    // 차량 등 회전된(Oriented) 3D 직육면체 박스
    addOrientedBox(cx, cy, cz, length, width, height, angle, color, topColor = null) {
      const c = color;
      const tc = topColor || color;
      const hl = length * 0.5;
      const hw = width * 0.5;
      const cosA = Math.cos(angle);
      const sinA = Math.sin(angle);

      const fx = cosA * hl, fy = sinA * hl;
      const rx = -sinA * hw, ry = cosA * hw;

      const z0 = cz;
      const z1 = cz + height;

      const p1 = [cx + fx + rx, cy + fy + ry, z0];
      const p2 = [cx - fx + rx, cy - fy + ry, z0];
      const p3 = [cx - fx - rx, cy - fy - ry, z0];
      const p4 = [cx + fx - rx, cy + fy - ry, z0];

      const tp1 = [p1[0], p1[1], z1];
      const tp2 = [p2[0], p2[1], z1];
      const tp3 = [p3[0], p3[1], z1];
      const tp4 = [p4[0], p4[1], z1];

      this.addQuad(tp1, tp2, tp3, tp4, [0, 0, 1], tc);
      this.addQuad(p4, p3, p2, p1, [0, 0, -1], c);
      this.addQuad(p1, p2, tp2, tp1, [-sinA, cosA, 0], c);
      this.addQuad(p2, p3, tp3, tp2, [-cosA, -sinA, 0], c);
      this.addQuad(p3, p4, tp4, tp3, [sinA, -cosA, 0], c);
      this.addQuad(p4, p1, tp1, tp4, [cosA, sinA, 0], c);
    }

    addPillar(x, y, z0, z1, radius, color, segs = 8) {
      const r = color[0], g = color[1], b = color[2], a = color[3] !== undefined ? color[3] : 1.0;
      for (let i = 0; i < segs; i++) {
        const th1 = (i / segs) * Math.PI * 2;
        const th2 = ((i + 1) / segs) * Math.PI * 2;
        const c1 = Math.cos(th1), s1 = Math.sin(th1);
        const c2 = Math.cos(th2), s2 = Math.sin(th2);

        const p1 = [x + c1 * radius, y + s1 * radius, z0];
        const p2 = [x + c2 * radius, y + s2 * radius, z0];
        const p3 = [x + c2 * radius, y + s2 * radius, z1];
        const p4 = [x + c1 * radius, y + s1 * radius, z1];
        const n = [(c1 + c2) * 0.5, (s1 + s2) * 0.5, 0];
        this.addQuad(p1, p2, p3, p4, n, [r, g, b, a]);
      }
    }

    // 원형 연석 링 (회전교차로 중앙 교통섬 등)
    addCurbRing(cx, cy, z0, z1, radius, width, curbColor, innerColor) {
      const segs = 16;
      const rOuter = radius;
      const rInner = Math.max(0, radius - width);

      for (let i = 0; i < segs; i++) {
        const th1 = (i / segs) * Math.PI * 2;
        const th2 = ((i + 1) / segs) * Math.PI * 2;
        const c1 = Math.cos(th1), s1 = Math.sin(th1);
        const c2 = Math.cos(th2), s2 = Math.sin(th2);

        // 연석 윗면
        const p1 = [cx + c1 * rInner, cy + s1 * rInner, z1];
        const p2 = [cx + c2 * rInner, cy + s2 * rInner, z1];
        const p3 = [cx + c2 * rOuter, cy + s2 * rOuter, z1];
        const p4 = [cx + c1 * rOuter, cy + s1 * rOuter, z1];
        this.addQuad(p1, p2, p3, p4, [0, 0, 1], curbColor);

        // 연석 외벽
        const w1 = [cx + c1 * rOuter, cy + s1 * rOuter, z0];
        const w2 = [cx + c2 * rOuter, cy + s2 * rOuter, z0];
        this.addQuad(w1, w2, p3, p4, [(c1 + c2) * 0.5, (s1 + s2) * 0.5, 0], curbColor);

        // 안쪽 잔디 디스크
        if (innerColor && rInner > 0) {
          const ip1 = [cx, cy, z1];
          const ip2 = [cx + c1 * rInner, cy + s1 * rInner, z1];
          const ip3 = [cx + c2 * rInner, cy + s2 * rInner, z1];
          this.addTriangle(ip1, ip2, ip3, [0, 0, 1], innerColor);
        }
      }
    }

    // 유선형 아치 볼트 지붕 (환승센터 및 체육관 돔)
    addCurvedVault(x, y, zBase, w, h, archHeight, color, segs = 10) {
      for (let i = 0; i < segs; i++) {
        const u1 = i / segs;
        const u2 = (i + 1) / segs;
        const x1 = x + u1 * w;
        const x2 = x + u2 * w;

        // 포물선 아치 높이
        const z1 = zBase + Math.sin(u1 * Math.PI) * archHeight;
        const z2 = zBase + Math.sin(u2 * Math.PI) * archHeight;

        const p1 = [x1, y, z1];
        const p2 = [x2, y, z2];
        const p3 = [x2, y + h, z2];
        const p4 = [x1, y + h, z1];

        const slope = (z2 - z1) / (x2 - x1);
        const norm = [-slope, 0, 1];
        const len = Math.hypot(norm[0], norm[2]);
        norm[0] /= len; norm[2] /= len;

        this.addQuad(p1, p2, p3, p4, norm, color);
      }
    }

    // 다양한 수종의 3D 나무 생성 (소나무, 벚나무, 활엽수)
    addTree(x, y, z, height = 12, radius = 5, treeType = 'deciduous') {
      if (treeType === 'pine') {
        // 한국 전통 적송/소나무 (적갈색 줄기 + 비대칭 단지형 수관)
        this.addPillar(x, y, z, z + height * 0.55, 0.9, [0.44, 0.28, 0.18]);
        this.addBox(x - radius * 0.9, y - radius * 0.7, z + height * 0.45, radius * 1.8, radius * 1.4, height * 0.3, [0.14, 0.45, 0.22]);
        this.addBox(x - radius * 0.6, y - radius * 0.9, z + height * 0.65, radius * 1.4, radius * 1.6, height * 0.35, [0.18, 0.52, 0.26]);
      } else if (treeType === 'cherry') {
        // 수변 벚꽃나무 (연분홍 화려한 수관)
        this.addPillar(x, y, z, z + height * 0.35, 0.7, [0.38, 0.26, 0.20]);
        this.addBox(x - radius, y - radius, z + height * 0.3, radius * 2, radius * 2, height * 0.45, [0.96, 0.75, 0.82]);
        this.addBox(x - radius * 0.75, y - radius * 0.75, z + height * 0.65, radius * 1.5, radius * 1.5, height * 0.35, [0.98, 0.82, 0.88]);
      } else {
        // 도심 느티나무 및 일반 활엽수
        this.addPillar(x, y, z, z + height * 0.4, 0.8, [0.36, 0.25, 0.18]);
        this.addBox(x - radius, y - radius, z + height * 0.35, radius * 2, radius * 2, height * 0.45, [0.22, 0.60, 0.30]);
        this.addBox(x - radius * 0.75, y - radius * 0.75, z + height * 0.65, radius * 1.5, radius * 1.5, height * 0.35, [0.28, 0.70, 0.34]);
      }
    }
  }

  // =======================================================================
  // 3D 조감도 뷰어 클래스
  // =======================================================================
  class CityView3D {
    constructor(simulator, canvas3D) {
      this.sim = simulator;
      this.canvas = canvas3D;
      this.gl = canvas3D.getContext('webgl', { antialias: true, alpha: false }) ||
                canvas3D.getContext('experimental-webgl');

      if (!this.gl) {
        console.error('WebGL is not supported in this environment.');
        return;
      }

      // 32비트 인덱스 버퍼 확장
      this.uintExt = this.gl.getExtension('OES_element_index_uint');

      // 카메라 상태 (기본값: 레퍼런스 조감도 시점: 아파트와 학교를 전면에 두고 하천 너머 환승센터/테크노밸리를 조망)
      this.camera = {
        target: { x: 1200, y: 1050, z: 0 },
        yaw: 0,              // 0도: 북쪽에서 남쪽을 내려다보는 조감도 최적 시점
        pitch: 0.54,         // 약 31도 부감 기울기
        distance: 1520,      // 카메라 거리
        fov: 42 * (Math.PI / 180)
      };

      this.isAutoRotating = false;
      this.isPanning = false;
      this.isOrbiting = false;
      this.lastMouse = { x: 0, y: 0 };
      this.keys = {};

      // 정적 메쉬 캐시
      this.staticMesh = null;
      this.staticBuffers = null;
      this.isDirty = true;

      // 동적 차량 메쉬
      this.dynamicBuffers = null;

      // 셰이더 초기화
      this.initShaders();
      this.bindEvents();
      this.resize();
    }

    initShaders() {
      const gl = this.gl;
      const vs = this.compileShader(gl.VERTEX_SHADER, VERTEX_SHADER_SRC);
      const fs = this.compileShader(gl.FRAGMENT_SHADER, FRAGMENT_SHADER_SRC);

      this.program = gl.createProgram();
      gl.attachShader(this.program, vs);
      gl.attachShader(this.program, fs);
      gl.linkProgram(this.program);

      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
        console.error('Shader Link Error:', gl.getProgramInfoLog(this.program));
      }

      this.attribs = {
        position: gl.getAttribLocation(this.program, 'a_position'),
        normal: gl.getAttribLocation(this.program, 'a_normal'),
        color: gl.getAttribLocation(this.program, 'a_color')
      };

      this.uniforms = {
        pvMatrix: gl.getUniformLocation(this.program, 'u_pvMatrix'),
        lightDir: gl.getUniformLocation(this.program, 'u_lightDir'),
        cameraPos: gl.getUniformLocation(this.program, 'u_cameraPos'),
        fogColor: gl.getUniformLocation(this.program, 'u_fogColor')
      };
    }

    compileShader(type, src) {
      const gl = this.gl;
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error('Shader compile failed:', gl.getShaderInfoLog(s));
      }
      return s;
    }

    markDirty() {
      this.isDirty = true;
    }

    resize() {
      if (!this.canvas) return;
      const w = this.canvas.parentElement.clientWidth;
      const h = this.canvas.parentElement.clientHeight;
      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width = w;
        this.canvas.height = h;
        if (this.gl) this.gl.viewport(0, 0, w, h);
      }
    }

    bindEvents() {
      window.addEventListener('resize', () => this.resize());

      // 마우스 인터랙션 (좌클릭 드래그: 회전/기울기, 우클릭 드래그: 팬, 휠: 줌)
      this.canvas.addEventListener('mousedown', (e) => {
        if (e.button === 0) {
          this.isOrbiting = true;
          this.lastMouse = { x: e.clientX, y: e.clientY };
        } else if (e.button === 2 || e.button === 1) {
          this.isPanning = true;
          this.lastMouse = { x: e.clientX, y: e.clientY };
        }
      });

      window.addEventListener('mousemove', (e) => {
        if (!this.isOrbiting && !this.isPanning) return;
        const dx = e.clientX - this.lastMouse.x;
        const dy = e.clientY - this.lastMouse.y;
        this.lastMouse = { x: e.clientX, y: e.clientY };

        if (this.isOrbiting) {
          this.camera.yaw += dx * 0.005;
          this.camera.pitch -= dy * 0.004;
          this.camera.pitch = Math.max(0.18, Math.min(1.48, this.camera.pitch));
        } else if (this.isPanning) {
          const panSpeed = this.camera.distance * 0.0012;
          const sinY = Math.sin(this.camera.yaw);
          const cosY = Math.cos(this.camera.yaw);
          this.camera.target.x -= (cosY * dx + sinY * dy) * panSpeed;
          this.camera.target.y -= (-sinY * dx + cosY * dy) * panSpeed;
        }
      });

      window.addEventListener('mouseup', () => {
        this.isOrbiting = false;
        this.isPanning = false;
      });

      this.canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const factor = e.deltaY > 0 ? 1.08 : 0.92;
        this.camera.distance = Math.max(220, Math.min(3600, this.camera.distance * factor));
      }, { passive: false });

      this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());

      window.addEventListener('keydown', (e) => {
        const k = e.key.toLowerCase();
        this.keys[k] = true;
      });
      window.addEventListener('keyup', (e) => {
        const k = e.key.toLowerCase();
        this.keys[k] = false;
      });
    }

    setPresetView(type) {
      if (type === 'south') {
        // 전면 조감도 (레퍼런스 조감도 앵글)
        this.camera.yaw = 0;
        this.camera.pitch = 0.54;
        this.camera.distance = 1520;
        this.camera.target = { x: 1200, y: 1050, z: 0 };
      } else if (type === 'isometric') {
        // 대각선 45도 아이소메트릭 조감도
        this.camera.yaw = Math.PI * 0.75;
        this.camera.pitch = 0.65;
        this.camera.distance = 1450;
        this.camera.target = { x: 1200, y: 1100, z: 0 };
      } else if (type === 'low') {
        // 저각 도심 가로 뷰
        this.camera.yaw = 0.15;
        this.camera.pitch = 0.22;
        this.camera.distance = 680;
        this.camera.target = { x: 1200, y: 800, z: 0 };
      } else if (type === 'top') {
        // 수직 부감 탑다운
        this.camera.yaw = 0;
        this.camera.pitch = 1.48;
        this.camera.distance = 1600;
        this.camera.target = { x: 1200, y: 1100, z: 0 };
      }
    }

    toggleAutoRotate() {
      this.isAutoRotating = !this.isAutoRotating;
      return this.isAutoRotating;
    }

    updateControls(dt) {
      const dtSec = Math.min(dt / 1000, 0.1);
      if (this.isAutoRotating && !this.isOrbiting) {
        this.camera.yaw += 0.15 * dtSec;
      }

      const speed = this.camera.distance * 0.65 * dtSec;
      const sinY = Math.sin(this.camera.yaw);
      const cosY = Math.cos(this.camera.yaw);

      if (this.keys['w'] || this.keys['arrowup']) {
        this.camera.target.x -= sinY * speed;
        this.camera.target.y += cosY * speed;
      }
      if (this.keys['s'] || this.keys['arrowdown']) {
        this.camera.target.x += sinY * speed;
        this.camera.target.y -= cosY * speed;
      }
      if (this.keys['a'] || this.keys['arrowleft']) {
        this.camera.target.x -= cosY * speed;
        this.camera.target.y -= sinY * speed;
      }
      if (this.keys['d'] || this.keys['arrowright']) {
        this.camera.target.x += cosY * speed;
        this.camera.target.y += sinY * speed;
      }
      if (this.keys['q']) this.camera.yaw -= 1.2 * dtSec;
      if (this.keys['e']) this.camera.yaw += 1.2 * dtSec;
      if (this.keys['r']) this.camera.pitch = Math.min(1.48, this.camera.pitch + 0.9 * dtSec);
      if (this.keys['f']) this.camera.pitch = Math.max(0.18, this.camera.pitch - 0.9 * dtSec);
    }

    // ===================================================================
    // 한국형 신도시 3D 지오메트리 고화질 빌드
    // ===================================================================
    buildStaticMesh() {
      const mesh = new MeshData();
      const sim = this.sim;

      // 1. 대지 지형 (Green Plains) & 웅장한 원경 산맥 (Mountain Ridges)
      this.buildTerrainAndMountains(mesh);

      // 2. 생태 하천과 수변공원 (Waterside Park & River)
      this.buildRiverAndParks(mesh);

      // 3. 도로망, 남북 주간선대로, BRT 및 입체교차로 (Roads & Interchange)
      this.buildRoadNetworkAndInterchange(mesh);

      // 3-1. 고품질 기준 구역 (Benchmark Area): 중앙 BRT 대로 및 수변 교차로/대형 교량 정밀 렌더링
      this.buildBenchmarkCentralCorridor(mesh);

      // 4. 원형 회전교차로 (Roundabouts) 3D 정밀 렌더링
      this.buildRoundabouts(mesh);

      // 5. 구역별 고품질 3D 건축 에셋 (아파트, 학교·운동장, 환승센터, 테크노밸리, 상업타워)
      this.buildHighQualityBuildings(mesh);

      // WebGL 버퍼 생성 및 업로드
      this.uploadStaticMesh(mesh);
    }

    // 1. 지형 및 웅장한 산맥 능선 메쉬
    buildTerrainAndMountains(mesh) {
      const riverY0 = 944, riverY1 = 1104;
      const groundColor = [0.28, 0.42, 0.25];

      // 중심 신도시 평탄 대지
      mesh.addQuad([-1200, -1200, 0], [3600, -1200, 0], [3600, riverY0, 0], [-1200, riverY0, 0], [0, 0, 1], groundColor);
      mesh.addQuad([-1200, riverY1, 0], [3600, riverY1, 0], [3600, 3400, 0], [-1200, 3400, 0], [0, 0, 1], groundColor);
      mesh.addQuad([-1200, riverY0, 0], [-200, riverY0, 0], [-200, riverY1, 0], [-1200, riverY1, 0], [0, 0, 1], groundColor);
      mesh.addQuad([2600, riverY0, 0], [3600, riverY0, 0], [3600, riverY1, 0], [2600, riverY1, 0], [0, 0, 1], groundColor);

      // 원경 병풍 산맥 능선 (남북 양방향에 웅장한 능선 구축)
      const mtnSegW = 100;
      for (let x = -1200; x < 3600; x += mtnSegW) {
        // 원경(Y > 2200): 북쪽/남쪽 배경 산맥
        const h3 = 260 + Math.sin(x * 0.0035) * 110 + Math.cos(x * 0.008) * 60;
        mesh.addBox(x, 2600, 0, mtnSegW, 350, h3, [0.15, 0.24, 0.16], [0.18, 0.28, 0.18]);
        const h2 = 185 + Math.cos(x * 0.005) * 85 + Math.sin(x * 0.011) * 45;
        mesh.addBox(x, 2300, 0, mtnSegW, 300, h2, [0.18, 0.28, 0.18], [0.22, 0.34, 0.22]);

        // 전경(Y < -200): 남측/북측 배경 구릉 산맥
        const hs3 = 240 + Math.cos(x * 0.004) * 95 + Math.sin(x * 0.009) * 50;
        mesh.addBox(x, -950, 0, mtnSegW, 300, hs3, [0.15, 0.24, 0.16], [0.18, 0.28, 0.18]);
        const hs2 = 170 + Math.sin(x * 0.0055) * 75;
        mesh.addBox(x, -650, 0, mtnSegW, 250, hs2, [0.18, 0.28, 0.18], [0.22, 0.34, 0.22]);
      }

      // 동측 및 서측 감싸는 자연 구릉지
      for (let y = -800; y < 2800; y += 140) {
        if (y > riverY0 - 80 && y < riverY1 + 80) continue;
        const hw = 95 + Math.sin(y * 0.007) * 45;
        mesh.addBox(-1000, y, 0, 350, 140, hw, [0.18, 0.28, 0.18], [0.22, 0.34, 0.21]);
        const he = 110 + Math.cos(y * 0.006) * 55;
        mesh.addBox(3050, y, 0, 350, 140, he, [0.18, 0.28, 0.18], [0.22, 0.34, 0.21]);
      }
    }

    // 2. 생태 하천과 수변공원 렌더러
    buildRiverAndParks(mesh) {
      const riverY0 = 944, riverY1 = 1104;

      // 하천 본류 맑은 에메랄드 수면 (스펙큘러 광택 a = 1.35)
      const waterColor = [0.12, 0.52, 0.78, 1.35];
      mesh.addQuad([-600, riverY0 + 20, -0.4], [3000, riverY0 + 20, -0.4], [3000, riverY1 - 20, -0.4], [-600, riverY1 - 20, -0.4], [0, 0, 1], waterColor);
      mesh.addQuad([-600, riverY0 + 20, -2.5], [3000, riverY0 + 20, -2.5], [3000, riverY1 - 20, -2.5], [-600, riverY1 - 20, -2.5], [0, 0, 1], [0.08, 0.25, 0.38]);

      // 호안 석축 제방 경사면
      const shoreColor = [0.55, 0.58, 0.62];
      mesh.addQuad([-600, riverY0 + 6, 0], [3000, riverY0 + 6, 0], [3000, riverY0 + 20, -0.4], [-600, riverY0 + 20, -0.4], [0, -0.5, 0.8], shoreColor);
      mesh.addQuad([-600, riverY1 - 20, -0.4], [3000, riverY1 - 20, -0.4], [3000, riverY1 - 6, 0], [-600, riverY1 - 6, 0], [0, 0.5, 0.8], shoreColor);

      // 하천 중간 모래톱/하중도 (Gravel Shoals & Reed Beds)
      for (const islX of [350, 1050, 1750]) {
        mesh.addBox(islX, (riverY0 + riverY1) * 0.5 - 12, -0.3, 85, 24, 0.45, [0.68, 0.65, 0.52], [0.32, 0.62, 0.35]);
        mesh.addTree(islX + 25, (riverY0 + riverY1) * 0.5, 0.15, 6, 2.5, 'deciduous');
        mesh.addTree(islX + 60, (riverY0 + riverY1) * 0.5, 0.15, 6.5, 2.8, 'deciduous');
      }

      // 수변 친수 계단 스탠드 (Waterside Amphitheater)
      for (const stepX of [720, 1550]) {
        for (let st = 0; st < 5; st++) {
          mesh.addBox(stepX, riverY0 + 4 + st * 3.2, -0.4 + st * 0.1, 140, 3.2, 0.16, [0.78, 0.80, 0.82]);
        }
      }

      // 수변공원 넓은 잔디 광장 및 산책로
      const parkLawnColor = [0.30, 0.64, 0.35];
      mesh.addQuad([-400, 880, 0.05], [2800, 880, 0.05], [2800, riverY0, 0.05], [-400, riverY0, 0.05], [0, 0, 1], parkLawnColor);
      mesh.addQuad([-400, riverY1, 0.05], [2800, riverY1, 0.05], [2800, 1165, 0.05], [-400, 1165, 0.05], [0, 0, 1], parkLawnColor);

      // 붉은색 수변 자전거 전용도로
      mesh.addQuad([-400, 895, 0.1], [2800, 895, 0.1], [2800, 902, 0.1], [-400, 902, 0.1], [0, 0, 1], [0.78, 0.25, 0.22]);
      mesh.addQuad([-400, 1146, 0.1], [2800, 1146, 0.1], [2800, 1153, 0.1], [-400, 1153, 0.1], [0, 0, 1], [0.78, 0.25, 0.22]);

      // 수변 만개한 분홍 벚나무 & 소나무 군락
      for (let tx = 80; tx < 2400; tx += 48) {
        mesh.addTree(tx, 915, 0.1, 12, 4.8, 'cherry');
        mesh.addTree(tx + 24, 930, 0.1, 10, 4.2, 'deciduous');
        mesh.addTree(tx + 12, 1130, 0.1, 12, 4.8, 'cherry');
        mesh.addTree(tx + 36, 1115, 0.1, 11, 4.5, 'deciduous');
      }

      // 수변 잔디 원형 야외공연장 (Circular Sunken Lawn)
      mesh.addCurbRing(1950, 920, 0.05, 0.35, 32, 3.5, [0.82, 0.85, 0.88], [0.24, 0.62, 0.32]);
    }

    // 3. 도로망, 남북 간선대로, BRT 및 입체교차로
    buildRoadNetworkAndInterchange(mesh) {
      const sim = this.sim;
      const nodeMap = new Map();
      for (const n of sim.nodes) nodeMap.set(n.id, n);

      for (const r of sim.roads) {
        const fNode = nodeMap.get(r.from);
        const tNode = nodeMap.get(r.to);
        if (!fNode || !tNode) continue;

        const zF = fNode.z || 0;
        const zT = tNode.z || 0;
        const isElevated = (zF > 1 || zT > 1 || r.gradeSeparated || r.bridge);
        const width = r.type === 'highway' ? 24 : (r.type === 'arterial' ? 16 : (r.type === 'parkway' ? 6 : 11));

        const dx = tNode.x - fNode.x;
        const dy = tNode.y - fNode.y;
        const len = Math.hypot(dx, dy);
        if (len < 0.5) continue;

        const ux = -dy / len;
        const uy = dx / len;
        const halfW = width * 0.5;

        // 도로 아스팔트 상판
        const p1 = [fNode.x + ux * halfW, fNode.y + uy * halfW, zF + 0.12];
        const p2 = [tNode.x + ux * halfW, tNode.y + uy * halfW, zT + 0.12];
        const p3 = [tNode.x - ux * halfW, tNode.y - uy * halfW, zT + 0.12];
        const p4 = [fNode.x - ux * halfW, fNode.y - uy * halfW, zF + 0.12];

        const asphaltColor = isElevated ? [0.20, 0.22, 0.26] : [0.18, 0.20, 0.23];
        mesh.addQuad(p1, p2, p3, p4, [0, 0, 1], asphaltColor);

        // 중앙 BRT 전용차로 (붉은색 유색 포장 노면)
        if (r.type === 'highway') {
          const brtW = 6.2;
          const bp1 = [fNode.x + ux * brtW * 0.5, fNode.y + uy * brtW * 0.5, zF + 0.16];
          const bp2 = [tNode.x + ux * brtW * 0.5, tNode.y + uy * brtW * 0.5, zT + 0.16];
          const bp3 = [tNode.x - ux * brtW * 0.5, tNode.y - uy * brtW * 0.5, zT + 0.16];
          const bp4 = [fNode.x - ux * brtW * 0.5, fNode.y - uy * brtW * 0.5, zF + 0.16];
          mesh.addQuad(bp1, bp2, bp3, bp4, [0, 0, 1], [0.82, 0.22, 0.24]);
        }

        // 고가 입체교차로 및 교량 구조물 (콘크리트 슬래브, 가드레일, 원형 교각)
        if (isElevated) {
          const slabThick = 1.4;
          const sp1 = [p1[0], p1[1], zF + 0.12 - slabThick];
          const sp2 = [p2[0], p2[1], zT + 0.12 - slabThick];
          const sp3 = [p3[0], p3[1], zT + 0.12 - slabThick];
          const sp4 = [p4[0], p4[1], zF + 0.12 - slabThick];
          mesh.addQuad(sp1, sp2, p2, p1, [ux, uy, 0], [0.55, 0.58, 0.62]);
          mesh.addQuad(p4, p3, sp3, sp4, [-ux, -uy, 0], [0.55, 0.58, 0.62]);
          mesh.addQuad(sp4, sp3, sp2, sp1, [0, 0, -1], [0.45, 0.48, 0.52]);

          // 외곽 콘크리트 가드레일 (방호벽)
          mesh.addQuad(p1, p2, [p2[0], p2[1], zT + 1.1], [p1[0], p1[1], zF + 1.1], [ux, uy, 0], [0.72, 0.75, 0.78]);
          mesh.addQuad([p4[0], p4[1], zF + 1.1], [p3[0], p3[1], zT + 1.1], p3, p4, [-ux, -uy, 0], [0.72, 0.75, 0.78]);

          // 고가 지지 2열 원형 교각 및 크로스빔(Pier Cap)
          const pierDist = 48;
          for (let s = 24; s < len - 12; s += pierDist) {
            const t = s / len;
            const px = fNode.x + dx * t;
            const py = fNode.y + dy * t;
            const pz = zF + (zT - zF) * t;
            if (pz > 2.0) {
              const capZ = pz - slabThick + 0.1;
              mesh.addBox(px - ux * halfW * 0.8 - 1.5, py - uy * halfW * 0.8 - 1.5, capZ - 1.2, 3.0, 3.0, 1.2, [0.65, 0.68, 0.72]);
              mesh.addPillar(px + ux * halfW * 0.5, py + uy * halfW * 0.5, 0, capZ - 1.0, 1.5, [0.68, 0.70, 0.73]);
              mesh.addPillar(px - ux * halfW * 0.5, py - uy * halfW * 0.5, 0, capZ - 1.0, 1.5, [0.68, 0.70, 0.73]);
            }
          }
        }

        // 수변 보행교 (아치 인도교)
        if (r.facility === 'pedestrian_bridge' && r.bridge) {
          const midX = (fNode.x + tNode.x) * 0.5;
          const midY = (fNode.y + tNode.y) * 0.5;
          mesh.addCurvedVault(midX - 22, midY - 3, 0.5, 44, 6, 9.5, [0.95, 0.96, 0.98, 1.2]);
          mesh.addPillar(midX - 18, midY, -0.4, 5.5, 0.6, [0.85, 0.88, 0.92]);
          mesh.addPillar(midX + 18, midY, -0.4, 5.5, 0.6, [0.85, 0.88, 0.92]);
        }
      }
    }

    // 3-1. 고품질 기준 구역 (Benchmark Area): 중앙 BRT 주간선대로 및 수변 교차로/대형 아치 교량 정밀 렌더러
    buildBenchmarkCentralCorridor(mesh) {
      const cx = 1200; // 중앙 BRT 주간선대로 중심 X 좌표

      // [A] 차선 점선 마킹 (Dashed White Lane Lines) & BRT 청색 경계선
      // Y = 460 ~ 1540 구간 정밀 마킹
      const segLen = 4.2;  // 점선 길이 4.2m
      const segGap = 4.8;  // 간격 4.8m
      const whitePaint = [0.96, 0.96, 0.98];
      const blueBrtLine = [0.15, 0.45, 0.90];
      const yellowDouble = [0.95, 0.78, 0.15];

      for (let y = 460; y <= 1540; y += (segLen + segGap)) {
        // 교차로 내부(횡단보도 부근)는 차선 점선 생략
        if ((y > 865 && y < 895) || (y > 1145 && y < 1175)) continue;

        // 일반 차선 분할 점선 (동측 +X: 1-2차선, 2-3차선 / 서측 -X: 1-2차선, 2-3차선)
        const laneOffsets = [6.2, 9.2, -6.2, -9.2];
        for (const off of laneOffsets) {
          mesh.addQuad(
            [cx + off - 0.12, y, 0.15],
            [cx + off + 0.12, y, 0.15],
            [cx + off + 0.12, y + segLen, 0.15],
            [cx + off - 0.12, y + segLen, 0.15],
            [0, 0, 1], whitePaint
          );
        }

        // BRT 청색 실선 경계선 (X = cx ± 3.4)
        mesh.addQuad(
          [cx + 3.4 - 0.15, y, 0.18],
          [cx + 3.4 + 0.15, y, 0.18],
          [cx + 3.4 + 0.15, y + segLen + segGap, 0.18],
          [cx + 3.4 - 0.15, y + segLen + segGap, 0.18],
          [0, 0, 1], blueBrtLine
        );
        mesh.addQuad(
          [cx - 3.4 - 0.15, y, 0.18],
          [cx - 3.4 + 0.15, y, 0.18],
          [cx - 3.4 + 0.15, y + segLen + segGap, 0.18],
          [cx - 3.4 - 0.15, y + segLen + segGap, 0.18],
          [0, 0, 1], blueBrtLine
        );

        // 도로 중앙 황색 복선 (X = cx ± 0.18)
        mesh.addQuad([cx - 0.30, y, 0.18], [cx - 0.10, y, 0.18], [cx - 0.10, y + segLen + segGap, 0.18], [cx - 0.30, y + segLen + segGap, 0.18], [0, 0, 1], yellowDouble);
        mesh.addQuad([cx + 0.10, y, 0.18], [cx + 0.30, y, 0.18], [cx + 0.30, y + segLen + segGap, 0.18], [cx + 0.10, y + segLen + segGap, 0.18], [0, 0, 1], yellowDouble);
      }

      // [B] 중앙 BRT 입체 정류장 2개소 (교량 남측 Y=840 & 북측 Y=1210)
      const stationYs = [840, 1210];
      for (const sy of stationYs) {
        const pLen = 40, pWid = 4.8, pH = 0.45;
        // 1) 승강장 화강석 연석 플랫폼
        mesh.addBox(cx - pWid * 0.5, sy - pLen * 0.5, 0.15, pWid, pLen, pH, [0.74, 0.76, 0.80], [0.82, 0.84, 0.88]);

        // 2) 가장자리 노란색 시각장애인 안전 점자블록 띠
        const yelBrd = [0.95, 0.82, 0.15];
        mesh.addQuad([cx - pWid * 0.5, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx - pWid * 0.5 + 0.38, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx - pWid * 0.5 + 0.38, sy + pLen * 0.5, 0.15 + pH + 0.02], [cx - pWid * 0.5, sy + pLen * 0.5, 0.15 + pH + 0.02], [0, 0, 1], yelBrd);
        mesh.addQuad([cx + pWid * 0.5 - 0.38, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx + pWid * 0.5, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx + pWid * 0.5, sy + pLen * 0.5, 0.15 + pH + 0.02], [cx + pWid * 0.5 - 0.38, sy + pLen * 0.5, 0.15 + pH + 0.02], [0, 0, 1], yelBrd);

        // 3) 미래형 유선형 글래스 캐노피 (Aerofoil Glass Shelter)
        const canW = 5.8, canL = 32, canH = 4.2;
        mesh.addCurvedVault(cx - canW * 0.5, sy - canL * 0.5, 0.15 + pH + 2.8, canW, canL, 1.3, [0.35, 0.70, 0.96, 1.45]);
        mesh.addBox(cx - canW * 0.5, sy - canL * 0.5, 0.15 + pH + 2.7, canW, canL, 0.15, [0.88, 0.90, 0.94]);

        // 4) 스테인리스 원형 기둥 4기
        for (const py of [sy - 11, sy - 3.5, sy + 3.5, sy + 11]) {
          mesh.addPillar(cx, py, 0.15 + pH, 0.15 + pH + 3.0, 0.28, [0.92, 0.94, 0.96]);
        }

        // 5) 승강장 내부 벤치 및 BIT(버스정보단말기)
        mesh.addBox(cx - 0.45, sy - 6.5, 0.15 + pH, 0.9, 4.2, 0.55, [0.35, 0.38, 0.42]);
        mesh.addBox(cx - 0.45, sy + 2.3, 0.15 + pH, 0.9, 4.2, 0.55, [0.35, 0.38, 0.42]);
        mesh.addBox(cx - 0.15, sy - 13.5, 0.15 + pH + 1.8, 0.3, 1.8, 0.9, [0.15, 0.18, 0.22], [0.20, 0.75, 0.95, 1.4]);

        // 6) 정류장 진입 보행 슬로프 램프
        mesh.addQuad(
          [cx - pWid * 0.5, sy - pLen * 0.5 - 4.5, 0.15],
          [cx + pWid * 0.5, sy - pLen * 0.5 - 4.5, 0.15],
          [cx + pWid * 0.5, sy - pLen * 0.5, 0.15 + pH],
          [cx - pWid * 0.5, sy - pLen * 0.5, 0.15 + pH],
          [0, -1, 1], [0.72, 0.74, 0.78]
        );
      }

      // [C] 수변 교차로 횡단보도 (Zebra Crossings) & 정지선 (Stop Lines)
      const crossYs = [880, 1160];
      for (const cy of crossYs) {
        // 1) 남북 간선대로 횡단보도 (동서 방향 횡단)
        const crossW = 6.4;
        const stripeW = 0.55;
        const stripeGap = 0.55;
        for (let sx = cx - 11.5; sx <= cx + 11.5; sx += (stripeW + stripeGap)) {
          mesh.addQuad(
            [sx, cy - crossW * 0.5, 0.16],
            [sx + stripeW, cy - crossW * 0.5, 0.16],
            [sx + stripeW, cy + crossW * 0.5, 0.16],
            [sx, cy + crossW * 0.5, 0.16],
            [0, 0, 1], whitePaint
          );
        }

        // 2) 정지선 (남북 양측에 각각 횡단보도 전방 3m 지점)
        for (const dy of [-crossW * 0.5 - 3.0, crossW * 0.5 + 3.0]) {
          mesh.addQuad(
            [cx - 12.0, cy + dy - 0.28, 0.16],
            [cx - 3.4, cy + dy - 0.28, 0.16],
            [cx - 3.4, cy + dy + 0.28, 0.16],
            [cx - 12.0, cy + dy + 0.28, 0.16],
            [0, 0, 1], whitePaint
          );
          mesh.addQuad(
            [cx + 3.4, cy + dy - 0.28, 0.16],
            [cx + 12.0, cy + dy - 0.28, 0.16],
            [cx + 12.0, cy + dy + 0.28, 0.16],
            [cx + 3.4, cy + dy + 0.28, 0.16],
            [0, 0, 1], whitePaint
          );
        }

        // 3) 교차로 L자형 신호등 철골 기둥 (Traffic Light Poles 4개소)
        const poleOffsets = [
          [cx - 13.5, cy - 8.5, 1],
          [cx + 13.5, cy - 8.5, -1],
          [cx - 13.5, cy + 8.5, 1],
          [cx + 13.5, cy + 8.5, -1]
        ];
        for (const [px, py, dir] of poleOffsets) {
          mesh.addPillar(px, py, 0.15, 7.8, 0.22, [0.22, 0.24, 0.28]);
          mesh.addBox(px, py - 0.15, 7.5, dir * 6.5, 0.3, 0.3, [0.22, 0.24, 0.28]);
          mesh.addBox(px + dir * 4.5, py - 0.25, 7.1, dir * 1.6, 0.5, 0.65, [0.15, 0.15, 0.18]);
          mesh.addBox(px + dir * 4.6, py - 0.30, 7.25, dir * 0.45, 0.15, 0.35, [0.15, 0.90, 0.35, 1.4]);
        }
      }

      // [D] 보도(인도) 및 차도 경계석 (Sidewalks & Granite Curbs)
      const swColor = [0.80, 0.82, 0.86];
      const curbColor = [0.65, 0.68, 0.72];
      for (const yBlock of [[480, 944], [1104, 1520]]) {
        const y0 = yBlock[0], y1 = yBlock[1];
        // 서측 보도 (폭 4m, 높이 0.22m)
        mesh.addBox(cx - 16.0, y0, 0.05, 4.0, y1 - y0, 0.22, swColor);
        mesh.addBox(cx - 12.35, y0, 0.05, 0.35, y1 - y0, 0.26, curbColor);

        // 동측 보도 (폭 4m, 높이 0.22m)
        mesh.addBox(cx + 12.0, y0, 0.05, 4.0, y1 - y0, 0.22, swColor);
        mesh.addBox(cx + 12.0, y0, 0.05, 0.35, y1 - y0, 0.26, curbColor);

        // 인도 위 가로등 및 2열 가로수
        for (let ly = y0 + 16; ly < y1 - 16; ly += 36) {
          // 서측 가로등
          mesh.addPillar(cx - 14.5, ly, 0.27, 9.2, 0.18, [0.85, 0.88, 0.92]);
          mesh.addBox(cx - 14.5, ly - 0.15, 8.9, 1.8, 0.3, 0.25, [0.95, 0.95, 0.98, 1.3]);
          // 서측 가로수
          mesh.addTree(cx - 18.0, ly + 18, 0.1, 13, 5.2, 'deciduous');

          // 동측 가로등
          mesh.addPillar(cx + 14.5, ly, 0.27, 9.2, 0.18, [0.85, 0.88, 0.92]);
          mesh.addBox(cx + 12.7, ly - 0.15, 8.9, 1.8, 0.3, 0.25, [0.95, 0.95, 0.98, 1.3]);
          // 동측 가로수
          mesh.addTree(cx + 18.0, ly + 18, 0.1, 13, 5.2, 'deciduous');
        }
      }

      // [E] 하천을 횡단하는 대형 교량 정밀 구조물 (Grand Waterfront Bridge Y=944 ~ 1104)
      const bY0 = 944, bY1 = 1104, bLen = bY1 - bY0;
      // 1) 교량 콘크리트 슬래브 (폭 29m, 두께 2.2m)
      mesh.addBox(cx - 14.5, bY0, -1.8, 29.0, bLen, 2.0, [0.55, 0.58, 0.62], [0.68, 0.70, 0.74]);

      // 2) 교량 외곽 안전 방호벽 및 화이트 난간 (White Bridge Railings)
      const railH = 1.3;
      // 서측 난간
      mesh.addBox(cx - 14.5, bY0, 0.2, 0.35, bLen, railH, [0.95, 0.96, 0.98]);
      mesh.addBox(cx - 14.6, bY0, 0.2 + railH - 0.12, 0.55, bLen, 0.12, [0.85, 0.88, 0.92]);
      // 동측 난간
      mesh.addBox(cx + 14.15, bY0, 0.2, 0.35, bLen, railH, [0.95, 0.96, 0.98]);
      mesh.addBox(cx + 14.05, bY0, 0.2 + railH - 0.12, 0.55, bLen, 0.12, [0.85, 0.88, 0.92]);

      // 3) 교량 하부 거대한 타원형 콘크리트 교각 6기
      for (const pierY of [bY0 + 35, bY0 + 80, bY0 + 125]) {
        mesh.addPillar(cx - 7.5, pierY, -3.0, -0.2, 2.4, [0.62, 0.65, 0.68], 12);
        mesh.addPillar(cx + 7.5, pierY, -3.0, -0.2, 2.4, [0.62, 0.65, 0.68], 12);
        mesh.addBox(cx - 10.0, pierY - 2.5, -0.6, 20.0, 5.0, 0.8, [0.58, 0.60, 0.64]);
      }

      // 4) 교량 상부 대형 화이트 아치 리브 & 서스펜션 케이블 (Tied-Arch Ribs)
      const archH = 32;
      mesh.addCurvedVault(cx - 14.8, bY0, 0.3, 1.6, bLen, archH, [0.96, 0.97, 0.99]);
      mesh.addCurvedVault(cx + 13.2, bY0, 0.3, 1.6, bLen, archH, [0.96, 0.97, 0.99]);
      for (let cy = bY0 + 20; cy < bY1 - 20; cy += 18) {
        const u = (cy - bY0) / bLen;
        const curArchZ = 0.3 + Math.sin(u * Math.PI) * archH;
        mesh.addPillar(cx - 14.0, cy, 0.3, curArchZ, 0.15, [0.88, 0.90, 0.95]);
        mesh.addPillar(cx + 14.0, cy, 0.3, curArchZ, 0.15, [0.88, 0.90, 0.95]);
      }

      // [F] 수변 교차로 주변 상가 스트리트몰 (Waterfront Street Malls)
      const mallCorners = [
        [cx - 52, 840, 1],
        [cx + 26, 840, -1],
        [cx - 52, 1180, 1],
        [cx + 26, 1180, -1]
      ];
      for (const [mx, my, dir] of mallCorners) {
        mesh.addBox(mx, my, 0.05, 26, 30, 0.25, [0.82, 0.80, 0.78]);
        const awningColor = dir > 0 ? [0.95, 0.45, 0.18] : [0.18, 0.48, 0.82];
        mesh.addBox(mx + 2, my + 2, 4.2, 22, 5, 0.4, awningColor);
        mesh.addPillar(mx + 6, my + 8, 0.3, 2.2, 0.08, [0.3, 0.3, 0.3]);
        mesh.addCurvedVault(mx + 4, my + 6, 2.2, 4.0, 4.0, 0.8, [0.95, 0.95, 0.98]);
        mesh.addPillar(mx + 16, my + 8, 0.3, 2.2, 0.08, [0.3, 0.3, 0.3]);
        mesh.addCurvedVault(mx + 14, my + 6, 2.2, 4.0, 4.0, 0.8, awningColor);
      }
    }

    // 4. 회전교차로 (Roundabout) 3D 렌더러
    buildRoundabouts(mesh) {
      const sim = this.sim;
      let rbs = sim.roundabouts ? [...sim.roundabouts] : [];

      if (rbs.length === 0 && sim.roads) {
        const centers = new Map();
        const orphanNodes = [];
        for (const r of sim.roads) {
          if (r.roundaboutCenter) {
            const key = `${Math.round(r.roundaboutCenter.x)}_${Math.round(r.roundaboutCenter.y)}`;
            if (!centers.has(key)) centers.set(key, { ...r.roundaboutCenter });
          } else if (r.facility === 'roundabout') {
            const fn = sim.nodes.find(n => n.id === r.from);
            const tn = sim.nodes.find(n => n.id === r.to);
            if (fn) orphanNodes.push(fn);
            if (tn) orphanNodes.push(tn);
          }
        }
        if (centers.size > 0) {
          rbs = Array.from(centers.values());
        } else if (orphanNodes.length >= 8) {
          const avgX = orphanNodes.reduce((s, n) => s + n.x, 0) / orphanNodes.length;
          const avgY = orphanNodes.reduce((s, n) => s + n.y, 0) / orphanNodes.length;
          const maxR = Math.max(...orphanNodes.map(n => Math.hypot(n.x - avgX, n.y - avgY)));
          rbs.push({ name: '회전교차로', x: avgX, y: avgY, radius: maxR > 5 ? maxR : 24 });
        }
      }

      for (const rb of rbs) {
        const cx = rb.x, cy = rb.y, radius = rb.radius || 24;
        const islandR = radius * 0.62;

        // 화강석 연석 링 + 중앙 에메랄드 잔디 디스크
        mesh.addCurbRing(cx, cy, 0.0, 0.45, islandR, 1.8, [0.85, 0.88, 0.90], [0.20, 0.60, 0.28]);

        // 중앙 2단 화단 턱 및 소나무 조경수
        mesh.addCurbRing(cx, cy, 0.45, 0.85, islandR * 0.52, 1.4, [0.75, 0.78, 0.80], [0.28, 0.66, 0.32]);
        mesh.addTree(cx, cy, 0.85, 15, 6.5, 'pine');

        // 주변 4방향 꽃나무 포인트
        for (let a = 0; a < 4; a++) {
          const ang = a * Math.PI * 0.5 + Math.PI * 0.25;
          const fx = cx + Math.cos(ang) * (islandR * 0.75);
          const fy = cy + Math.sin(ang) * (islandR * 0.75);
          mesh.addTree(fx, fy, 0.45, 7.5, 2.8, 'cherry');
        }

        // 회전교차로 교통섬 조명 볼라드 4기
        for (let a = 0; a < 4; a++) {
          const ang = a * Math.PI * 0.5;
          const bx = cx + Math.cos(ang) * (islandR * 0.95);
          const by = cy + Math.sin(ang) * (islandR * 0.95);
          mesh.addPillar(bx, by, 0.45, 1.6, 0.3, [0.95, 0.95, 0.85]);
        }
      }
    }

    // 5. 사용자 조감도에 맞춘 초고품질 3D 건축 에셋 빌더
    buildHighQualityBuildings(mesh) {
      const sim = this.sim;
      const blocks = sim.zoneBlocks || [];

      // 5-1. 특수 랜드마크 (초등학교와 운동장, 대형 복합환승센터)
      for (const b of blocks) {
        // [A] 초등학교와 규격 운동장 (초품아 캠퍼스)
        if (b.landUse === 'school') {
          // 1) 5층 현대식 본관 교사동 (L자형 매스)
          const schW = 76, schH = 26, schD = 18;
          mesh.addBox(b.x + 8, b.y + 12, 0, schW, schH, schD, [0.93, 0.92, 0.89], [0.70, 0.74, 0.78]);
          // 연결된 신관 윙
          mesh.addBox(b.x + 8, b.y + 12 + schH, 0, 24, 38, schD, [0.93, 0.92, 0.89], [0.70, 0.74, 0.78]);

          // 컬러풀 차양 루버 (노랑, 주황, 스카이블루 액센트 패널)
          for (let wx = b.x + 14; wx < b.x + schW - 8; wx += 14) {
            mesh.addBox(wx, b.y + 10, 4, 3.5, 2.0, schD - 6, [0.95, 0.68, 0.18]);
            mesh.addBox(wx + 6, b.y + 10, 4, 3.5, 2.0, schD - 6, [0.22, 0.65, 0.88]);
          }

          // 2) 둥근 볼트 지붕 실내 체육관·강당 윙
          mesh.addCurvedVault(b.x + 8, b.y + 12 + schH + 38, 0, 32, 28, 11, [0.35, 0.55, 0.78, 1.25]);

          // 교문 및 필로티 캐노피
          mesh.addBox(b.x + 36, b.y + 6, 0, 18, 8, 4.5, [0.22, 0.45, 0.78]);

          // 3) 대형 운동장 (8레인 우레탄 트랙 + 규격 인조잔디구장 + 골대 + 스탠드 차양막)
          const trkX = b.x + 92, trkY = b.y + 14, trkW = 94, trkH = 70;
          mesh.addQuad([trkX, trkY, 0.15], [trkX + trkW, trkY, 0.15], [trkX + trkW, trkY + trkH, 0.15], [trkX, trkY + trkH, 0.15], [0, 0, 1], [0.78, 0.24, 0.20]);
          mesh.addQuad([trkX + 3, trkY + 3, 0.17], [trkX + trkW - 3, trkY + 3, 0.17], [trkX + trkW - 3, trkY + trkH - 3, 0.17], [trkX + 3, trkY + trkH - 3, 0.17], [0, 0, 1], [0.96, 0.96, 0.96]);
          mesh.addQuad([trkX + 5, trkY + 5, 0.19], [trkX + trkW - 5, trkY + 5, 0.19], [trkX + trkW - 5, trkY + trkH - 5, 0.19], [trkX + 5, trkY + trkH - 5, 0.19], [0, 0, 1], [0.78, 0.24, 0.20]);

          // 내부 에메랄드 잔디 축구장
          const pitchInset = 9;
          mesh.addQuad(
            [trkX + pitchInset, trkY + pitchInset, 0.22], [trkX + trkW - pitchInset, trkY + pitchInset, 0.22],
            [trkX + trkW - pitchInset, trkY + trkH - pitchInset, 0.22], [trkX + pitchInset, trkY + trkH - pitchInset, 0.22],
            [0, 0, 1], [0.18, 0.65, 0.28]
          );

          // 축구 골대 2기
          mesh.addBox(trkX + pitchInset + 0.5, trkY + trkH * 0.5 - 7, 0.22, 1.8, 14, 4.5, [0.98, 0.98, 0.98]);
          mesh.addBox(trkX + trkW - pitchInset - 2.3, trkY + trkH * 0.5 - 7, 0.22, 1.8, 14, 4.5, [0.98, 0.98, 0.98]);

          // 스탠드 관람석 및 곡면 차양막 (Tensile Canopy)
          mesh.addBox(trkX + pitchInset, trkY + trkH - pitchInset, 0.2, trkW - pitchInset * 2, 6, 2.5, [0.78, 0.80, 0.82]);
          mesh.addCurvedVault(trkX + pitchInset + 10, trkY + trkH - pitchInset, 2.5, trkW - pitchInset * 2 - 20, 6, 4.5, [0.95, 0.95, 0.98, 1.2]);

          // 다목적 농구 코트
          mesh.addBox(b.x + 8, b.y + b.h - 26, 0.15, 30, 20, 0.1, [0.22, 0.48, 0.78]);

          // 학교 주변 조경수
          for (let sx = b.x + 6; sx < b.x + b.w - 12; sx += 32) {
            mesh.addTree(sx, b.y + b.h - 6, 0.1, 9, 3.5, 'cherry');
          }
        }

        // [B] 대형 복합환승센터 (초대형 유선형 에어로포일 아치 돔 + 글래스 아트리움)
        else if (b.landUse === 'transit') {
          const transW = Math.max(b.w, 130), transH = b.h - 16;
          mesh.addBox(b.x - 20, b.y + 8, 0, transW + 20, transH, 5.5, [0.38, 0.40, 0.44], [0.45, 0.48, 0.52]);

          const archH = 34;
          mesh.addCurvedVault(b.x - 24, b.y + 12, 5.5, transW + 28, transH - 10, archH, [0.88, 0.90, 0.95, 1.35]);

          for (let ry = b.y + 20; ry < b.y + transH; ry += 32) {
            mesh.addCurvedVault(b.x - 26, ry, 5.5, transW + 32, 4.0, archH + 1.4, [0.96, 0.97, 0.99]);
          }

          mesh.addBox(b.x - 16, b.y + transH - 6, 0, transW + 12, 6, 26, [0.22, 0.58, 0.88, 1.45]);

          for (let by = b.y + 18; by < b.y + transH - 24; by += 32) {
            mesh.addBox(b.x - 45, by, 0.2, 22, 22, 4.0, [0.92, 0.94, 0.98, 1.25], [0.35, 0.65, 0.88]);
          }

          mesh.addBox(b.x - 55, b.y + transH * 0.5 - 6, 7.5, 40, 12, 4.5, [0.25, 0.55, 0.82, 1.35]);
        }
      }

      // 5-2. 주거 슈퍼블록, 중심상업, 테크노밸리 건축 에셋 고화질 배치
      for (const cell of sim.zoneCells.values()) {
        if (!cell.type) continue;
        if (cell.landUse === 'school' || cell.landUse === 'transit' || cell.landUse === 'river') continue;

        // 1) 한국형 고품격 아파트 대단지 (Residential Superblocks)
        if (cell.type === 'residential') {
          if (cell.x % 64 === 0 && cell.y % 48 === 0) {
            const isTower = (cell.x % 128 === 0 && cell.y % 96 === 0);
            const aptW = isTower ? 34 : 58;
            const aptD = isTower ? 34 : 18;
            const stories = isTower ? 28 + ((cell.x + cell.y) % 6) : 20 + ((cell.x * 7 + cell.y * 11) % 8);
            const aptHeight = stories * 3.2; // 64m ~ 108m

            mesh.addPillar(cell.x + 6, cell.y + 4, 0, 4.8, 0.9, [0.42, 0.45, 0.48]);
            mesh.addPillar(cell.x + aptW - 6, cell.y + 4, 0, 4.8, 0.9, [0.42, 0.45, 0.48]);
            mesh.addPillar(cell.x + 6, cell.y + aptD - 4, 0, 4.8, 0.9, [0.42, 0.45, 0.48]);
            mesh.addPillar(cell.x + aptW - 6, cell.y + aptD - 4, 0, 4.8, 0.9, [0.42, 0.45, 0.48]);
            mesh.addBox(cell.x + 10, cell.y + 3, 0, aptW - 20, aptD - 6, 4.8, [0.25, 0.48, 0.68, 1.25]);

            mesh.addBox(cell.x + 2, cell.y + 2, 4.8, aptW - 4, aptD - 4, aptHeight - 4.8, [0.94, 0.94, 0.95]);
            mesh.addBox(cell.x + aptW * 0.5 - 4, cell.y + 1, 4.8, 8, aptD - 2, aptHeight - 3, [0.26, 0.28, 0.34]);

            const accentColor = (cell.x % 128 === 0) ? [0.88, 0.35, 0.22] : [0.18, 0.48, 0.85];
            mesh.addBox(cell.x + 1.5, cell.y + 1.5, aptHeight - 6, aptW - 3, aptD - 3, 2.5, accentColor);

            for (let fz = 8; fz < aptHeight - 8; fz += 6.4) {
              mesh.addBox(cell.x + 4, cell.y + 0.5, fz, aptW * 0.36, 1.5, 2.4, [0.20, 0.24, 0.30, 1.2]);
              mesh.addBox(cell.x + aptW * 0.56, cell.y + 0.5, fz, aptW * 0.36, 1.5, 2.4, [0.20, 0.24, 0.30, 1.2]);
            }

            mesh.addBox(cell.x + aptW * 0.5 - 7, cell.y + aptD * 0.5 - 6, aptHeight, 14, 12, 7.5, [0.58, 0.62, 0.68], [0.88, 0.90, 0.95]);
            mesh.addBox(cell.x + 6, cell.y + 4, aptHeight, 14, 14, 0.6, [0.48, 0.50, 0.54], [0.85, 0.25, 0.22]);

            if (cell.x % 128 === 0) {
              mesh.addBox(cell.x - 22, cell.y + 4, 0.1, 20, 20, 0.1, [0.26, 0.62, 0.32]);
              mesh.addBox(cell.x - 18, cell.y + 8, 0.15, 12, 12, 0.1, [0.94, 0.58, 0.22]);
              mesh.addBox(cell.x - 14, cell.y + 12, 0.25, 4, 4, 3.8, [0.95, 0.85, 0.18]);
            }

            mesh.addTree(cell.x - 8, cell.y + 10, 0.1, 13, 5.0, 'pine');
            mesh.addTree(cell.x + aptW + 8, cell.y + 10, 0.1, 12, 4.6, 'cherry');
          }
        }

        // 2) 중심상업지구 글래스 타워 & 쇼핑몰 (Commercial)
        else if (cell.type === 'commercial') {
          if (cell.x % 48 === 0 && cell.y % 48 === 0) {
            const comW = 42, comH = 40;
            const comHeight = 65 + ((cell.x * 19 + cell.y * 37) % 65);

            mesh.addBox(cell.x + 3, cell.y + 3, 0, comW - 6, comH - 6, comHeight, [0.22, 0.55, 0.88, 1.35], [0.24, 0.68, 0.35]);
            mesh.addBox(cell.x + 2, cell.y + 2, comHeight * 0.35, comW - 4, comH - 4, 2.0, [0.94, 0.95, 0.98]);
            mesh.addBox(cell.x + 2, cell.y + 2, comHeight * 0.70, comW - 4, comH - 4, 2.0, [0.94, 0.95, 0.98]);

            mesh.addBox(cell.x - 2, cell.y - 2, 0, comW + 4, comH + 4, 15, [0.44, 0.47, 0.52], [0.35, 0.65, 0.35]);
            mesh.addBox(cell.x + 4, cell.y - 6, 0, 18, 6, 5.0, [0.95, 0.68, 0.18]);
          }
        }

        // 3) 판교형 테크노밸리 R&D 캠퍼스 (Industrial)
        else if (cell.type === 'industrial') {
          if (cell.x % 64 === 0 && cell.y % 48 === 0) {
            const rdW = 58, rdH = 38;
            const rdHeight = 35 + ((cell.x + cell.y) % 25);

            mesh.addBox(cell.x + 4, cell.y + 4, 0, rdW, rdH, rdHeight, [0.32, 0.62, 0.88, 1.35], [0.28, 0.68, 0.35]);

            for (let lz = 6; lz < rdHeight; lz += 7.5) {
              mesh.addBox(cell.x + 3, cell.y + 3, lz, rdW + 2, rdH + 2, 0.9, [0.95, 0.96, 0.98]);
            }

            mesh.addBox(cell.x + 8, cell.y + 8, rdHeight, rdW * 0.42, rdH - 16, 1.2, [0.28, 0.68, 0.35]);
            mesh.addBox(cell.x + rdW * 0.52, cell.y + 8, rdHeight, rdW * 0.42, rdH - 16, 1.5, [0.12, 0.18, 0.38]);

            if (cell.x % 128 === 0) {
              mesh.addBox(cell.x + rdW + 4, cell.y + rdH * 0.5 - 4, rdHeight * 0.62, 24, 8, 4.8, [0.25, 0.55, 0.85, 1.35]);
            }

            mesh.addBox(cell.x + rdW * 0.3, cell.y + rdH * 0.3, 0.1, 18, 14, 0.15, [0.12, 0.52, 0.85, 1.4]);
          }
        }
      }
    }

    uploadStaticMesh(mesh) {
      const gl = this.gl;
      if (!this.staticBuffers) {
        this.staticBuffers = {
          pos: gl.createBuffer(),
          norm: gl.createBuffer(),
          col: gl.createBuffer(),
          idx: gl.createBuffer(),
          count: 0
        };
      }

      gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuffers.pos);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.positions), gl.STATIC_DRAW);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuffers.norm);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.normals), gl.STATIC_DRAW);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuffers.col);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.colors), gl.STATIC_DRAW);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.staticBuffers.idx);
      if (this.uintExt) {
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(mesh.indices), gl.STATIC_DRAW);
        this.indexType = gl.UNSIGNED_INT;
      } else {
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(mesh.indices), gl.STATIC_DRAW);
        this.indexType = gl.UNSIGNED_SHORT;
      }

      this.staticBuffers.count = mesh.indices.length;
      this.isDirty = false;
    }

    // ===================================================================
    // 실시간 3D 차량 시뮬레이션 렌더링
    // ===================================================================
    renderCars() {
      const sim = this.sim;
      if (!sim || !sim.cars || sim.cars.length === 0) return;

      const gl = this.gl;
      const mesh = new MeshData();
      const nodeMap = new Map();
      for (const n of sim.nodes) nodeMap.set(n.id, n);

      for (const car of sim.cars) {
        const road = sim.roads[car.roadIndex];
        if (!road) continue;
        const fNode = nodeMap.get(road.from);
        const tNode = nodeMap.get(road.to);
        if (!fNode || !tNode) continue;

        const roadLen = (road.length > 0) ? road.length : Math.hypot(tNode.x - fNode.x, tNode.y - fNode.y);
        const t = roadLen > 0 ? Math.max(0, Math.min(1.0, car.progress / roadLen)) : 0;
        const zF = fNode.z || 0;
        const zT = tNode.z || 0;

        let curX, curY, angle;
        if (road.midPoint) {
          const mp = road.midPoint;
          const omt = 1 - t;
          curX = omt * omt * fNode.x + 2 * omt * t * mp.x + t * t * tNode.x;
          curY = omt * omt * fNode.y + 2 * omt * t * mp.y + t * t * tNode.y;
          const dx = 2 * (1 - t) * (mp.x - fNode.x) + 2 * t * (tNode.x - mp.x);
          const dy = 2 * (1 - t) * (mp.y - fNode.y) + 2 * t * (tNode.y - mp.y);
          angle = Math.atan2(dy, dx);
        } else {
          curX = fNode.x + (tNode.x - fNode.x) * t;
          curY = fNode.y + (tNode.y - fNode.y) * t;
          angle = Math.atan2(tNode.y - fNode.y, tNode.x - fNode.x);
        }
        const curZ = zF + (zT - zF) * t + 0.35;

        const isBrt = (road.type === 'highway');
        const carLen = isBrt ? 11.0 : 4.6;
        const carWid = isBrt ? 3.4 : 2.2;
        const carH = isBrt ? 3.6 : 1.8;

        const carColor = isBrt ? [0.92, 0.18, 0.22] : (car.color === '#e74c3c' ? [0.88, 0.22, 0.22] : [0.92, 0.92, 0.95]);
        const topColor = isBrt ? [0.82, 0.15, 0.18] : [0.35, 0.38, 0.42];

        // 차량 주행 각도(angle)에 맞춘 회전 3D 박스
        mesh.addOrientedBox(curX, curY, curZ, carLen, carWid, carH, angle, carColor, topColor);

        // 헤드라이트 (앞범퍼 조명)
        const hlDist = carLen * 0.48;
        const hlX = curX + Math.cos(angle) * hlDist;
        const hlY = curY + Math.sin(angle) * hlDist;
        mesh.addOrientedBox(hlX, hlY, curZ + 0.3, 0.4, carWid * 0.75, 0.45, angle, [1.0, 1.0, 0.85, 1.4]);
      }

      if (mesh.indices.length === 0) return;

      if (!this.dynamicBuffers) {
        this.dynamicBuffers = {
          pos: gl.createBuffer(),
          norm: gl.createBuffer(),
          col: gl.createBuffer(),
          idx: gl.createBuffer()
        };
      }

      gl.bindBuffer(gl.ARRAY_BUFFER, this.dynamicBuffers.pos);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.positions), gl.DYNAMIC_DRAW);
      gl.vertexAttribPointer(this.attribs.position, 3, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(this.attribs.position);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.dynamicBuffers.norm);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.normals), gl.DYNAMIC_DRAW);
      gl.vertexAttribPointer(this.attribs.normal, 3, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(this.attribs.normal);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.dynamicBuffers.col);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.colors), gl.DYNAMIC_DRAW);
      gl.vertexAttribPointer(this.attribs.color, 4, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(this.attribs.color);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.dynamicBuffers.idx);
      if (this.uintExt) {
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(mesh.indices), gl.DYNAMIC_DRAW);
        gl.drawElements(gl.TRIANGLES, mesh.indices.length, gl.UNSIGNED_INT, 0);
      } else {
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(mesh.indices), gl.DYNAMIC_DRAW);
        gl.drawElements(gl.TRIANGLES, mesh.indices.length, gl.UNSIGNED_SHORT, 0);
      }
    }

    // ===================================================================
    // 3D 렌더 프레임 루프
    // ===================================================================
    render(dt = 16) {
      const gl = this.gl;
      if (!gl) return;

      this.updateControls(dt);

      if (this.isDirty || !this.staticBuffers) {
        this.buildStaticMesh();
      }

      gl.enable(gl.DEPTH_TEST);
      gl.depthFunc(gl.LEQUAL);

      // 한국 신도시 맑은 하늘 배경색 (#8ebbde)
      gl.clearColor(0.56, 0.73, 0.88, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      gl.useProgram(this.program);

      const aspect = this.canvas.width / this.canvas.height;
      const proj = Mat4.create();
      Mat4.perspective(proj, this.camera.fov, aspect, 10.0, 7500.0);

      const eyeX = this.camera.target.x - this.camera.distance * Math.cos(this.camera.pitch) * Math.sin(this.camera.yaw);
      const eyeY = this.camera.target.y - this.camera.distance * Math.cos(this.camera.pitch) * Math.cos(this.camera.yaw);
      const eyeZ = this.camera.target.z + this.camera.distance * Math.sin(this.camera.pitch);

      const view = Mat4.create();
      Mat4.lookAt(view, [eyeX, eyeY, eyeZ], [this.camera.target.x, this.camera.target.y, this.camera.target.z], [0, 0, 1]);

      const pvMatrix = Mat4.create();
      Mat4.multiply(pvMatrix, proj, view);

      gl.uniformMatrix4fv(this.uniforms.pvMatrix, false, pvMatrix);
      // 화사한 정오 태양광
      gl.uniform3f(this.uniforms.lightDir, -0.42, -0.65, 0.64);
      gl.uniform3f(this.uniforms.cameraPos, eyeX, eyeY, eyeZ);
      gl.uniform3f(this.uniforms.fogColor, 0.62, 0.76, 0.90);

      if (this.staticBuffers && this.staticBuffers.count > 0) {
        gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuffers.pos);
        gl.vertexAttribPointer(this.attribs.position, 3, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(this.attribs.position);

        gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuffers.norm);
        gl.vertexAttribPointer(this.attribs.normal, 3, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(this.attribs.normal);

        gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuffers.col);
        gl.vertexAttribPointer(this.attribs.color, 4, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(this.attribs.color);

        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.staticBuffers.idx);
        gl.drawElements(gl.TRIANGLES, this.staticBuffers.count, this.indexType || (this.uintExt ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT), 0);
      }

      this.renderCars();
    }
  }

  global.CityView3D = CityView3D;
})(typeof window !== 'undefined' ? window : this);
'''

with open(r'C:\Users\sims\Desktop\시티즈\view3d.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("view3d.js updated with Benchmark Corridor!")
