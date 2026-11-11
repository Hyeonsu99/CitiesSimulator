// =======================================================================
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

    // 원형 / 다각형 실린더 입체 프리즘 (로툰다 원형 타워 및 돔 기단)
    addCylinder(cx, cy, z0, z1, radius, color, topColor, segs = 12) {
      const tc = topColor || color;
      const r = color[0], g = color[1], b = color[2], a = color[3] !== undefined ? color[3] : 1.0;
      for (let i = 0; i < segs; i++) {
        const th1 = (i / segs) * Math.PI * 2;
        const th2 = ((i + 1) / segs) * Math.PI * 2;
        const c1 = Math.cos(th1), s1 = Math.sin(th1);
        const c2 = Math.cos(th2), s2 = Math.sin(th2);

        // 측면
        const p1 = [cx + c1 * radius, cy + s1 * radius, z0];
        const p2 = [cx + c2 * radius, cy + s2 * radius, z0];
        const p3 = [cx + c2 * radius, cy + s2 * radius, z1];
        const p4 = [cx + c1 * radius, cy + s1 * radius, z1];
        const n = [(c1 + c2) * 0.5, (s1 + s2) * 0.5, 0];
        this.addQuad(p1, p2, p3, p4, n, [r, g, b, a]);

        // 상단 캡
        const tp1 = [cx, cy, z1];
        const tp2 = [cx + c1 * radius, cy + s1 * radius, z1];
        const tp3 = [cx + c2 * radius, cy + s2 * radius, z1];
        this.addTriangle(tp1, tp2, tp3, [0, 0, 1], tc);
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

    // Y축 방향 유선형 아치 볼트 지붕 및 교량 아치 리브 (len 방향 아치)
    addCurvedVaultY(x, y, zBase, w, len, archHeight, color, segs = 16) {
      for (let i = 0; i < segs; i++) {
        const u1 = i / segs;
        const u2 = (i + 1) / segs;
        const y1 = y + u1 * len;
        const y2 = y + u2 * len;

        const z1 = zBase + Math.sin(u1 * Math.PI) * archHeight;
        const z2 = zBase + Math.sin(u2 * Math.PI) * archHeight;

        const p1 = [x, y1, z1];
        const p2 = [x + w, y1, z1];
        const p3 = [x + w, y2, z2];
        const p4 = [x, y2, z2];

        const slope = (z2 - z1) / (y2 - y1);
        const norm = [0, -slope, 1];
        const nlen = Math.hypot(norm[1], norm[2]);
        norm[1] /= nlen; norm[2] /= nlen;

        this.addQuad(p1, p2, p3, p4, norm, color);
      }
    }

    // 초고화질 다층 수형 3D 가로수 및 조경수 (소나무, 벚나무, 수양버들, 은행나무, 느티나무, 관목)
    addTree(x, y, z, height = 12, radius = 5, treeType = 'deciduous') {
      if (treeType === 'pine') {
        // 한국 전통 적송/해송 (곡선형 적갈색 줄기 + 비대칭 3단 구름형 수관 + 음영)
        this.addPillar(x, y, z, z + height * 0.42, 0.85, [0.46, 0.28, 0.16]);
        this.addPillar(x + 0.35, y - 0.25, z + height * 0.40, z + height * 0.70, 0.65, [0.46, 0.28, 0.16]);
        // 1단 하부 수관 패드 (동남향)
        this.addBox(x - radius * 0.4, y - radius * 1.1, z + height * 0.40, radius * 1.6, radius * 1.3, height * 0.22, [0.12, 0.38, 0.18], [0.16, 0.46, 0.22]);
        // 2단 중부 수관 패드 (서북향)
        this.addBox(x - radius * 1.1, y - radius * 0.4, z + height * 0.58, radius * 1.5, radius * 1.5, height * 0.24, [0.13, 0.40, 0.19], [0.18, 0.48, 0.24]);
        // 3단 상부 정수리 수관
        this.addBox(x - radius * 0.65, y - radius * 0.65, z + height * 0.76, radius * 1.3, radius * 1.3, height * 0.20, [0.15, 0.44, 0.22], [0.20, 0.52, 0.26]);
      } else if (treeType === 'cherry') {
        // 수변 화사한 왕벚나무 (연분홍 3단 볼륨 화관 + 밝은 하이라이트)
        this.addPillar(x, y, z, z + height * 0.38, 0.72, [0.38, 0.26, 0.20]);
        this.addBox(x - radius * 1.05, y - radius * 0.95, z + height * 0.28, radius * 2.1, radius * 1.9, height * 0.38, [0.96, 0.72, 0.80], [0.99, 0.84, 0.89]);
        this.addBox(x - radius * 0.85, y - radius * 0.85, z + height * 0.55, radius * 1.7, radius * 1.7, height * 0.34, [0.98, 0.78, 0.85], [1.0, 0.88, 0.92]);
        this.addBox(x - radius * 0.45, y - radius * 0.45, z + height * 0.80, radius * 0.9, radius * 0.9, height * 0.22, [0.99, 0.86, 0.91], [1.0, 0.92, 0.95]);
      } else if (treeType === 'willow') {
        // 수변 수양버들 (늘어진 버들가지 4단 다층 볼륨)
        this.addPillar(x, y, z, z + height * 0.65, 0.88, [0.40, 0.30, 0.22]);
        this.addBox(x - radius * 0.75, y - radius * 0.75, z + height * 0.55, radius * 1.5, radius * 1.5, height * 0.35, [0.32, 0.65, 0.26], [0.38, 0.72, 0.30]);
        this.addBox(x - radius * 1.15, y - radius * 1.15, z + height * 0.32, radius * 2.3, radius * 2.3, height * 0.30, [0.28, 0.60, 0.24], [0.34, 0.68, 0.28]);
        this.addBox(x - radius * 1.35, y - radius * 1.35, z + height * 0.14, radius * 2.7, radius * 2.7, height * 0.22, [0.25, 0.55, 0.22], [0.30, 0.62, 0.25]);
      } else if (treeType === 'ginkgo') {
        // 황금빛 가을 은행나무 (피라미드형 다단 층상 수관)
        this.addPillar(x, y, z, z + height * 0.55, 0.75, [0.42, 0.32, 0.24]);
        this.addBox(x - radius * 0.95, y - radius * 0.95, z + height * 0.30, radius * 1.9, radius * 1.9, height * 0.28, [0.92, 0.75, 0.12], [0.96, 0.82, 0.16]);
        this.addBox(x - radius * 0.72, y - radius * 0.72, z + height * 0.52, radius * 1.44, radius * 1.44, height * 0.28, [0.95, 0.80, 0.14], [0.98, 0.86, 0.18]);
        this.addBox(x - radius * 0.45, y - radius * 0.45, z + height * 0.74, radius * 0.9, radius * 0.9, height * 0.26, [0.98, 0.85, 0.16], [1.0, 0.90, 0.22]);
      } else if (treeType === 'shrub' || treeType === 'hedge') {
        // 단지/도로변 정원 관목 (둥근 회양목/철쭉)
        this.addBox(x - radius * 0.7, y - radius * 0.7, z, radius * 1.4, radius * 1.4, height * 0.75, [0.22, 0.58, 0.25], [0.28, 0.68, 0.32]);
        this.addBox(x - radius * 0.5, y - radius * 0.5, z + height * 0.65, radius * 1.0, radius * 1.0, height * 0.35, [0.26, 0.64, 0.28], [0.32, 0.74, 0.36]);
      } else {
        // 도심 웅장한 느티나무 및 대형 활엽수 (원형 돔형 차양 수관)
        this.addPillar(x, y, z, z + height * 0.45, 0.90, [0.36, 0.25, 0.18]);
        this.addBox(x - radius * 1.1, y - radius * 1.0, z + height * 0.32, radius * 2.2, radius * 2.0, height * 0.36, [0.18, 0.50, 0.24], [0.24, 0.58, 0.28]);
        this.addBox(x - radius * 0.85, y - radius * 0.85, z + height * 0.60, radius * 1.7, radius * 1.7, height * 0.34, [0.22, 0.58, 0.28], [0.28, 0.66, 0.32]);
        this.addBox(x - radius * 0.5, y - radius * 0.5, z + height * 0.85, radius * 1.0, radius * 1.0, height * 0.22, [0.26, 0.64, 0.30], [0.32, 0.72, 0.36]);
      }
    }
  }

  // =======================================================================
  // 3D 건축물 발자국(Footprint) AABB 충돌 방지 및 이격거리 관리 시스템
  // 도로, 특수부지, 하천, 회전교차로 및 건물 상호 간 겹침 0건 보장
  // =======================================================================
  class FootprintManager {
    constructor() {
      this.boxes = []; // { minX, minY, maxX, maxY, tag, meta }
    }

    addBox(minX, minY, maxX, maxY, tag = '', meta = null) {
      this.boxes.push({ minX, minY, maxX, maxY, tag, meta });
    }

    isOverlapping(minX, minY, maxX, maxY, buildingMargin = 6.0) {
      for (let i = 0; i < this.boxes.length; i++) {
        const b = this.boxes[i];
        const m = b.tag.startsWith('building') ? buildingMargin : 1.0;
        if (minX - m < b.maxX && maxX + m > b.minX && minY - m < b.maxY && maxY + m > b.minY) {
          return true;
        }
      }
      return false;
    }

    clear() {
      this.boxes = [];
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

    // 2. 생태 하천과 수변공원 렌더러 (다단 자연석 호안, 마리나 폰툰, 수변카페 파빌리온, 키네틱 조형물)
    buildRiverAndParks(mesh) {
      const riverY0 = 944, riverY1 = 1104;

      // 하천 본류 맑은 에메랄드 수면 (스펙큘러 광택 a = 1.35)
      const waterColor = [0.12, 0.52, 0.78, 1.35];
      mesh.addQuad([-600, riverY0 + 20, -0.4], [3000, riverY0 + 20, -0.4], [3000, riverY1 - 20, -0.4], [-600, riverY1 - 20, -0.4], [0, 0, 1], waterColor);
      mesh.addQuad([-600, riverY0 + 20, -2.5], [3000, riverY0 + 20, -2.5], [3000, riverY1 - 20, -2.5], [-600, riverY1 - 20, -2.5], [0, 0, 1], [0.08, 0.25, 0.38]);

      // 호안 석축 제방 경사면 및 자연석 바위 호안
      const shoreColor = [0.55, 0.58, 0.62];
      mesh.addQuad([-600, riverY0 + 6, 0], [3000, riverY0 + 6, 0], [3000, riverY0 + 20, -0.4], [-600, riverY0 + 20, -0.4], [0, -0.5, 0.8], shoreColor);
      mesh.addQuad([-600, riverY1 - 20, -0.4], [3000, riverY1 - 20, -0.4], [3000, riverY1 - 6, 0], [-600, riverY1 - 6, 0], [0, 0.5, 0.8], shoreColor);

      // 다단 자연석 호안 립랩 (Riprap Stones)
      for (let rx = 100; rx < 2600; rx += 72) {
        mesh.addBox(rx, riverY0 + 17, -0.35, 6.0, 3.5, 0.45, [0.62, 0.64, 0.66]);
        mesh.addBox(rx + 36, riverY1 - 20, -0.35, 6.0, 3.5, 0.45, [0.62, 0.64, 0.66]);
        mesh.addTree(rx + 14, riverY0 + 18, -0.2, 3.5, 1.5, 'shrub'); // 수생 갈대/관목 군락
        mesh.addTree(rx + 50, riverY1 - 18, -0.2, 3.5, 1.5, 'shrub');
      }

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

      // 수변 만개한 벚나무, 소나무, 수양버들, 은행나무의 풍성한 다층 식생
      for (let tx = 80; tx < 2400; tx += 48) {
        mesh.addTree(tx, 915, 0.1, 12, 4.8, (tx % 96 === 0) ? 'willow' : 'cherry');
        mesh.addTree(tx + 24, 930, 0.1, 10, 4.2, (tx % 144 === 0) ? 'ginkgo' : 'deciduous');
        mesh.addTree(tx + 12, 1130, 0.1, 12, 4.8, (tx % 96 === 0) ? 'pine' : 'cherry');
        mesh.addTree(tx + 36, 1115, 0.1, 11, 4.5, (tx % 144 === 0) ? 'willow' : 'deciduous');
      }

      // 수변 전망 목재 데크 2개소 (Observatory Wooden Decks with Railings & Shading)
      for (const dX of [520, 1450]) {
        // 돌출 목재 데크 플랫폼
        mesh.addBox(dX - 14, riverY0 + 6, 0.12, 28, 14, 0.28, [0.65, 0.52, 0.40]);
        // 안전 목재 난간
        mesh.addBox(dX - 14, riverY0 + 19, 0.40, 28, 0.4, 0.9, [0.45, 0.35, 0.25]);
        mesh.addBox(dX - 14, riverY0 + 6, 0.40, 0.4, 13, 0.9, [0.45, 0.35, 0.25]);
        mesh.addBox(dX + 13.6, riverY0 + 6, 0.40, 0.4, 13, 0.9, [0.45, 0.35, 0.25]);
        // 수변 휴게 정자 파고라 (Timber Pergola)
        mesh.addPillar(dX - 8, riverY0 + 10, 0.40, 3.8, 0.22, [0.42, 0.32, 0.24]);
        mesh.addPillar(dX + 8, riverY0 + 10, 0.40, 3.8, 0.22, [0.42, 0.32, 0.24]);
        mesh.addBox(dX - 10, riverY0 + 8, 3.8, 20, 4.5, 0.25, [0.55, 0.42, 0.30]);
        // 목재 벤치 2조
        mesh.addBox(dX - 7, riverY0 + 9, 0.40, 4.5, 1.2, 0.45, [0.42, 0.32, 0.24]);
        mesh.addBox(dX + 2.5, riverY0 + 9, 0.40, 4.5, 1.2, 0.45, [0.42, 0.32, 0.24]);
      }

      // [신규 1] 수변 마리나 폰툰 계류장 & 카약/보트 선착장 (Floating Leisure Boat Pontoon)
      const dockX = 880;
      mesh.addBox(dockX - 2.0, riverY0 + 4, -0.15, 4.0, 14.0, 0.20, [0.55, 0.42, 0.32]);
      mesh.addBox(dockX - 2.0, riverY0 + 4, 0.05, 0.15, 14.0, 0.85, [0.72, 0.75, 0.78]); // 좌측 난간
      mesh.addBox(dockX + 1.85, riverY0 + 4, 0.05, 0.15, 14.0, 0.85, [0.72, 0.75, 0.78]); // 우측 난간
      mesh.addBox(dockX - 14, riverY0 + 18, -0.32, 28, 12, 0.38, [0.62, 0.50, 0.38], [0.68, 0.55, 0.42]);
      mesh.addPillar(dockX - 11, riverY0 + 29, 0.06, 0.65, 0.22, [0.88, 0.90, 0.94]);
      mesh.addPillar(dockX + 11, riverY0 + 29, 0.06, 0.65, 0.22, [0.88, 0.90, 0.94]);
      mesh.addPillar(dockX - 11, riverY0 + 19, 0.06, 0.65, 0.22, [0.88, 0.90, 0.94]);
      mesh.addPillar(dockX + 11, riverY0 + 19, 0.06, 0.65, 0.22, [0.88, 0.90, 0.94]);
      // 정박된 친환경 레저 보트 2척 (선체 & 윈드실드)
      mesh.addBox(dockX - 8, riverY0 + 28, -0.28, 4.8, 8.5, 1.2, [0.95, 0.96, 0.98], [0.18, 0.45, 0.85]);
      mesh.addBox(dockX - 7.5, riverY0 + 31.5, 0.92, 3.8, 2.5, 0.65, [0.25, 0.58, 0.85, 1.4]);
      mesh.addBox(dockX + 3.2, riverY0 + 28, -0.28, 4.8, 8.5, 1.2, [0.95, 0.96, 0.98], [0.88, 0.22, 0.25]);
      mesh.addBox(dockX + 3.7, riverY0 + 31.5, 0.92, 3.8, 2.5, 0.65, [0.25, 0.58, 0.85, 1.4]);

      // [신규 2] 수변 오픈 카페 테라스 및 화이트 텐실 셰이드 파빌리온
      const cafeX = 1780;
      mesh.addBox(cafeX - 12, riverY1 - 20, 0.08, 24, 14, 0.25, [0.68, 0.56, 0.44]);
      mesh.addPillar(cafeX - 9, riverY1 - 17, 0.33, 4.2, 0.18, [0.92, 0.94, 0.96]);
      mesh.addPillar(cafeX + 9, riverY1 - 17, 0.33, 4.2, 0.18, [0.92, 0.94, 0.96]);
      mesh.addPillar(cafeX - 9, riverY1 - 9, 0.33, 4.2, 0.18, [0.92, 0.94, 0.96]);
      mesh.addPillar(cafeX + 9, riverY1 - 9, 0.33, 4.2, 0.18, [0.92, 0.94, 0.96]);
      mesh.addCurvedVault(cafeX - 10.5, riverY1 - 18, 4.2, 21, 10, 2.2, [0.98, 0.98, 1.0, 1.2]);
      // 카페 야외 파라솔 및 티테이블 2조
      mesh.addBox(cafeX - 5, riverY1 - 14, 0.33, 2.2, 2.2, 0.72, [0.35, 0.38, 0.42]);
      mesh.addPillar(cafeX - 3.9, riverY1 - 12.9, 0.33, 2.8, 0.06, [0.85, 0.88, 0.90]);
      mesh.addBox(cafeX - 6.0, riverY1 - 15.0, 2.8, 4.2, 4.2, 0.35, [0.95, 0.92, 0.85]);
      mesh.addBox(cafeX + 3, riverY1 - 14, 0.33, 2.2, 2.2, 0.72, [0.35, 0.38, 0.42]);
      mesh.addPillar(cafeX + 4.1, riverY1 - 12.9, 0.33, 2.8, 0.06, [0.85, 0.88, 0.90]);
      mesh.addBox(cafeX + 2.0, riverY1 - 15.0, 2.8, 4.2, 4.2, 0.35, [0.95, 0.92, 0.85]);

      // [신규 3] 수변 랜드마크 키네틱 바람 조형물 (Civic Art Sculpture)
      mesh.addCurbRing(1360, 915, 0.05, 0.45, 7.5, 1.5, [0.85, 0.88, 0.92], [0.72, 0.75, 0.78]);
      mesh.addPillar(1360, 915, 0.5, 9.5, 0.35, [0.92, 0.94, 0.98]);
      mesh.addBox(1360 - 2.5, 915 - 0.4, 7.5, 5.0, 0.8, 1.8, [0.95, 0.78, 0.22, 1.4]);
      mesh.addBox(1360 - 0.4, 915 - 2.5, 8.8, 0.8, 5.0, 1.8, [0.22, 0.65, 0.95, 1.4]);

      // 수변 잔디 원형 야외공연장 (Circular Sunken Lawn)
      mesh.addCurbRing(1950, 920, 0.05, 0.35, 32, 3.5, [0.82, 0.85, 0.88], [0.24, 0.62, 0.32]);
    }

    // 3. 도로망, 남북 간선대로, BRT 및 입체교차로 (2차 베지어 곡선 일반화 렌더러)
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
        const halfW = width * 0.5;

        // 곡선 여부 및 세분화 스텝 수 계산
        const hasCurve = !!r.midPoint;
        const chordLen = Math.hypot(tNode.x - fNode.x, tNode.y - fNode.y);
        if (chordLen < 0.5 && !hasCurve) continue;

        const roadLen = r.length || chordLen;
        const steps = hasCurve ? Math.max(16, Math.min(32, Math.round(roadLen / 15))) : 1;

        // 2차 베지어 곡선(또는 직선) 상의 샘플 포인트 및 수직 단위 법선 계산 헬퍼
        const samplePoint = (t) => {
          let px, py, dx, dy;
          if (hasCurve) {
            const mp = r.midPoint;
            const omt = 1 - t;
            px = omt * omt * fNode.x + 2 * omt * t * mp.x + t * t * tNode.x;
            py = omt * omt * fNode.y + 2 * omt * t * mp.y + t * t * tNode.y;
            dx = 2 * (1 - t) * (mp.x - fNode.x) + 2 * t * (tNode.x - mp.x);
            dy = 2 * (1 - t) * (mp.y - fNode.y) + 2 * t * (tNode.y - mp.y);
          } else {
            px = fNode.x + (tNode.x - fNode.x) * t;
            py = fNode.y + (tNode.y - fNode.y) * t;
            dx = tNode.x - fNode.x;
            dy = tNode.y - fNode.y;
          }
          const tLen = Math.hypot(dx, dy) || 1.0;
          const ux = -dy / tLen;
          const uy = dx / tLen;
          const pz = zF + (zT - zF) * t;
          return { px, py, pz, ux, uy, dx: dx / tLen, dy: dy / tLen };
        };

        const asphaltColor = isElevated ? [0.20, 0.22, 0.26] : [0.18, 0.20, 0.23];
        const slabThick = 1.4;
        const isBrtRoad = r.facility === 'brt' || (r.type === 'highway' && r.facility !== 'expressway');
        const brtHalfW = (r.brtLanes ? r.brtLanes * 3.4 : 6.2) * 0.5;

        let prevS = samplePoint(0);

        for (let i = 1; i <= steps; i++) {
          const t = i / steps;
          const curS = samplePoint(t);

          // 1) 3D 아스팔트 노면 상판 쿼드
          const p1 = [prevS.px + prevS.ux * halfW, prevS.py + prevS.uy * halfW, prevS.pz + 0.12];
          const p2 = [curS.px + curS.ux * halfW, curS.py + curS.uy * halfW, curS.pz + 0.12];
          const p3 = [curS.px - curS.ux * halfW, curS.py - curS.uy * halfW, curS.pz + 0.12];
          const p4 = [prevS.px - prevS.ux * halfW, prevS.py - prevS.uy * halfW, prevS.pz + 0.12];
          mesh.addQuad(p1, p2, p3, p4, [0, 0, 1], asphaltColor);

          // 2) 중앙 BRT 전용차로 (붉은색 유색 포장 노면 및 청색 실선 구분선)
          if (isBrtRoad) {
            const bp1 = [prevS.px + prevS.ux * brtHalfW, prevS.py + prevS.uy * brtHalfW, prevS.pz + 0.15];
            const bp2 = [curS.px + curS.ux * brtHalfW, curS.py + curS.uy * brtHalfW, curS.pz + 0.15];
            const bp3 = [curS.px - curS.ux * brtHalfW, curS.py - curS.uy * brtHalfW, curS.pz + 0.15];
            const bp4 = [prevS.px - prevS.ux * brtHalfW, prevS.py - prevS.uy * brtHalfW, prevS.pz + 0.15];
            mesh.addQuad(bp1, bp2, bp3, bp4, [0, 0, 1], [0.82, 0.22, 0.24]);

            // 좌우 청색 BRT 실선
            const lineThick = 0.22;
            const bL1 = [prevS.px + prevS.ux * (brtHalfW + lineThick), prevS.py + prevS.uy * (brtHalfW + lineThick), prevS.pz + 0.16];
            const bL2 = [curS.px + curS.ux * (brtHalfW + lineThick), curS.py + curS.uy * (brtHalfW + lineThick), curS.pz + 0.16];
            mesh.addQuad(bp1, bp2, bL2, bL1, [0, 0, 1], [0.15, 0.45, 0.90]);

            const bR1 = [prevS.px - prevS.ux * (brtHalfW + lineThick), prevS.py - prevS.uy * (brtHalfW + lineThick), prevS.pz + 0.16];
            const bR2 = [curS.px - curS.ux * (brtHalfW + lineThick), curS.py - curS.uy * (brtHalfW + lineThick), curS.pz + 0.16];
            mesh.addQuad(bR1, bR2, bp3, bp4, [0, 0, 1], [0.15, 0.45, 0.90]);
          } else if (r.type === 'arterial') {
            // [보조간선]: 중앙 황색선
            const yW = 0.22;
            const yp1 = [prevS.px + prevS.ux * yW, prevS.py + prevS.uy * yW, prevS.pz + 0.15];
            const yp2 = [curS.px + curS.ux * yW, curS.py + curS.uy * yW, curS.pz + 0.15];
            const yp3 = [curS.px - curS.ux * yW, curS.py - curS.uy * yW, curS.pz + 0.15];
            const yp4 = [prevS.px - prevS.ux * yW, prevS.py - prevS.uy * yW, prevS.pz + 0.15];
            mesh.addQuad(yp1, yp2, yp3, yp4, [0, 0, 1], [0.95, 0.78, 0.15]);
          }

          // 3) 고가 입체교차로 및 교량 구조물 (콘크리트 슬래브, 가드레일 난간)
          if (isElevated) {
            const sp1 = [p1[0], p1[1], prevS.pz + 0.12 - slabThick];
            const sp2 = [p2[0], p2[1], curS.pz + 0.12 - slabThick];
            const sp3 = [p3[0], p3[1], curS.pz + 0.12 - slabThick];
            const sp4 = [p4[0], p4[1], prevS.pz + 0.12 - slabThick];

            const avgUx = (prevS.ux + curS.ux) * 0.5;
            const avgUy = (prevS.uy + curS.uy) * 0.5;

            // 좌측·우측 슬래브 측면 및 밑면
            mesh.addQuad(sp1, sp2, p2, p1, [avgUx, avgUy, 0], [0.55, 0.58, 0.62]);
            mesh.addQuad(p4, p3, sp3, sp4, [-avgUx, -avgUy, 0], [0.55, 0.58, 0.62]);
            mesh.addQuad(sp4, sp3, sp2, sp1, [0, 0, -1], [0.45, 0.48, 0.52]);

            // 외곽 콘크리트 가드레일 방호벽 난간
            const railH = 1.1;
            mesh.addQuad(p1, p2, [p2[0], p2[1], curS.pz + 0.12 + railH], [p1[0], p1[1], prevS.pz + 0.12 + railH], [avgUx, avgUy, 0], [0.72, 0.75, 0.78]);
            mesh.addQuad([p4[0], p4[1], prevS.pz + 0.12 + railH], [p3[0], p3[1], curS.pz + 0.12 + railH], p3, p4, [-avgUx, -avgUy, 0], [0.72, 0.75, 0.78]);

            // 고가 입체도로 및 BRT 고속화 구간 투명 방음벽 (H빔 프레임 + 아크릴 차음 패널)
            if (isElevated && (r.type === 'highway' || r.facility === 'brt')) {
              const noiseH = 3.2;
              const soundGlassCol = [0.82, 0.92, 0.98, 1.35];
              const zBaseL = prevS.pz + 0.12 + railH;
              const zBaseR = curS.pz + 0.12 + railH;
              mesh.addQuad([p1[0], p1[1], zBaseL], [p2[0], p2[1], zBaseR], [p2[0], p2[1], zBaseR + noiseH], [p1[0], p1[1], zBaseL + noiseH], [avgUx, avgUy, 0], soundGlassCol);
              mesh.addQuad([p4[0], p4[1], zBaseL + noiseH], [p3[0], p3[1], zBaseR + noiseH], [p3[0], p3[1], zBaseR], [p4[0], p4[1], zBaseL], [-avgUx, -avgUy, 0], soundGlassCol);
              // 상부 H빔 캡
              mesh.addQuad([p1[0], p1[1], zBaseL + noiseH], [p2[0], p2[1], zBaseR + noiseH], [p2[0] - avgUx * 0.18, p2[1] - avgUy * 0.18, zBaseR + noiseH], [p1[0] - avgUx * 0.18, p1[1] - avgUy * 0.18, zBaseL + noiseH], [0, 0, 1], [0.38, 0.42, 0.48]);
            }

            // 고가 방호벽 황색 위험 반사체 (16m 간격)
            if (isElevated && i % 2 === 0) {
              mesh.addBox(curS.px + curS.ux * (halfW - 0.15) - 0.2, curS.py + curS.uy * (halfW - 0.15) - 0.2, curS.pz + 0.7, 0.4, 0.4, 0.3, [0.98, 0.75, 0.15, 2.0]);
              mesh.addBox(curS.px - curS.ux * (halfW - 0.15) - 0.2, curS.py - curS.uy * (halfW - 0.15) - 0.2, curS.pz + 0.7, 0.4, 0.4, 0.3, [0.98, 0.75, 0.15, 2.0]);
            }
          }

          // 고속도로/간선도로 문형식 방향 안내 표지판 (Overhead Gantry Signs)
          if ((r.type === 'highway' || r.facility === 'brt') && steps >= 8 && i === Math.floor(steps * 0.5)) {
            const gz = curS.pz + 0.12;
            const gH = 7.5;
            const leftP = [curS.px + curS.ux * (halfW + 0.8), curS.py + curS.uy * (halfW + 0.8)];
            const rightP = [curS.px - curS.ux * (halfW + 0.8), curS.py - curS.uy * (halfW + 0.8)];
            mesh.addPillar(leftP[0], leftP[1], gz, gz + gH, 0.35, [0.38, 0.42, 0.48]);
            mesh.addPillar(rightP[0], rightP[1], gz, gz + gH, 0.35, [0.38, 0.42, 0.48]);
            mesh.addBox(curS.px - (halfW + 0.8), curS.py - 0.4, gz + gH - 0.6, (halfW + 0.8) * 2, 0.8, 0.8, [0.45, 0.48, 0.54]);
            const sW = halfW * 0.75, sH = 2.4;
            mesh.addBox(curS.px - halfW * 0.8, curS.py - 0.5, gz + gH - sH - 0.2, sW, 0.25, sH, [0.08, 0.48, 0.24]);
            mesh.addBox(curS.px + halfW * 0.05, curS.py - 0.5, gz + gH - sH - 0.2, sW, 0.25, sH, [0.08, 0.48, 0.24]);
          }

          prevS = curS;
        }

        // 4) 고가 지지 2열 원형 교각 및 크로스빔 (Pier Cap) - 곡선/직선 공통 간격 배치
        if (isElevated) {
          const pierDist = 48;
          for (let s = 24; s < roadLen - 12; s += pierDist) {
            const st = s / roadLen;
            const sp = samplePoint(st);
            if (sp.pz > 2.0) {
              const capZ = sp.pz - slabThick + 0.1;
              mesh.addBox(sp.px - sp.ux * halfW * 0.8 - 1.5, sp.py - sp.uy * halfW * 0.8 - 1.5, capZ - 1.2, 3.0, 3.0, 1.2, [0.65, 0.68, 0.72]);
              mesh.addPillar(sp.px + sp.ux * halfW * 0.5, sp.py + sp.uy * halfW * 0.5, 0, capZ - 1.0, 1.5, [0.68, 0.70, 0.73]);
              mesh.addPillar(sp.px - sp.ux * halfW * 0.5, sp.py - sp.uy * halfW * 0.5, 0, capZ - 1.0, 1.5, [0.68, 0.70, 0.73]);
            }
          }
        }

        // 5) 수변 보행교 (아치 인도교)
        if (r.facility === 'pedestrian_bridge' && r.bridge) {
          const midS = samplePoint(0.5);
          mesh.addCurvedVault(midS.px - 22, midS.py - 3, 0.5, 44, 6, 9.5, [0.95, 0.96, 0.98, 1.2]);
          mesh.addPillar(midS.px - 18, midS.py, -0.4, 5.5, 0.6, [0.85, 0.88, 0.92]);
          mesh.addPillar(midS.px + 18, midS.py, -0.4, 5.5, 0.6, [0.85, 0.88, 0.92]);
        }
      }
    }

    // 3-1. 고품질 기준 구역 (Benchmark Area): 중앙 BRT 대로 및 수변 교차로·대형 교량·친수공원·랜드마크 타워
    buildBenchmarkCentralCorridor(mesh) {
      const cx = 1200; // 중앙 BRT 주간선대로 중심 X 좌표

      // =================================================================
      // [A] 차로 노면 포장 (BRT 적색 아스콘) & 정밀 도로 마킹 (Lane Markings)
      // =================================================================
      const whitePaint = [0.96, 0.96, 0.98];
      const blueBrtLine = [0.15, 0.45, 0.90];
      const yellowDouble = [0.95, 0.78, 0.15];
      const brtRedAsphalt = [0.65, 0.22, 0.24]; // 한국 BRT 전용차로 적색 미끄럼방지 포장

      // 1) 중앙 BRT 차로 전체 적색 아스콘 포장 오버레이 (X = cx - 3.4 ~ cx + 3.4)
      for (const ySpan of [[460, 775], [825, 944], [944, 1104], [1104, 1175], [1225, 1540]]) {
        mesh.addQuad(
          [cx - 3.4, ySpan[0], 0.14],
          [cx + 3.4, ySpan[0], 0.14],
          [cx + 3.4, ySpan[1], 0.14],
          [cx - 3.4, ySpan[1], 0.14],
          [0, 0, 1], brtRedAsphalt
        );
      }

      // 2) 점선 차선 분할 마킹 & BRT 청색 경계선 & 중앙 황색 복선
      const segLen = 4.2;  // 점선 길이 4.2m
      const segGap = 4.8;  // 간격 4.8m

      for (let y = 460; y <= 1540; y += (segLen + segGap)) {
        // 교차로 내부(횡단보도 전후 20m)는 차선 점선 생략
        if ((y > 778 && y < 822) || (y > 1178 && y < 1222)) continue;

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
        mesh.addQuad([cx + 3.4 - 0.15, y, 0.18], [cx + 3.4 + 0.15, y, 0.18], [cx + 3.4 + 0.15, y + segLen + segGap, 0.18], [cx + 3.4 - 0.15, y + segLen + segGap, 0.18], [0, 0, 1], blueBrtLine);
        mesh.addQuad([cx - 3.4 - 0.15, y, 0.18], [cx - 3.4 + 0.15, y, 0.18], [cx - 3.4 + 0.15, y + segLen + segGap, 0.18], [cx - 3.4 - 0.15, y + segLen + segGap, 0.18], [0, 0, 1], blueBrtLine);

        // 도로 중앙 황색 복선 (X = cx ± 0.18, 정류장 제외 구간)
        if (!((y > 835 && y < 885) || (y > 1115 && y < 1165))) {
          mesh.addQuad([cx - 0.30, y, 0.18], [cx - 0.10, y, 0.18], [cx - 0.10, y + segLen + segGap, 0.18], [cx - 0.30, y + segLen + segGap, 0.18], [0, 0, 1], yellowDouble);
          mesh.addQuad([cx + 0.10, y, 0.18], [cx + 0.30, y, 0.18], [cx + 0.30, y + segLen + segGap, 0.18], [cx + 0.10, y + segLen + segGap, 0.18], [0, 0, 1], yellowDouble);
        }
      }

      // 3) BRT 전용차로 노면 다이아몬드 & "BUS" 표시
      for (const by of [520, 640, 720, 900, 1100, 1280, 1400]) {
        for (const bx of [cx - 1.7, cx + 1.7]) {
          // 백색 다이아몬드 기호
          mesh.addQuad([bx - 0.6, by, 0.16], [bx, by - 1.2, 0.16], [bx + 0.6, by, 0.16], [bx, by + 1.2, 0.16], [0, 0, 1], whitePaint);
          // "BUS" 문자 표시 사각 바
          mesh.addBox(bx - 0.5, by + 2.8, 0.16, 1.0, 1.6, 0.02, whitePaint);
        }
      }

      // 4) 일반 차로 횡단보도 예고 다이아몬드 및 직진 화살표
      for (const cy of [800, 1200]) {
        for (const sgn of [-1, 1]) {
          const dyAdvance = cy + sgn * 48; // 횡단보도 전방 약 48m 지점
          for (const lx of [cx - 7.7, cx + 7.7]) {
            mesh.addQuad([lx - 0.7, dyAdvance, 0.16], [lx, dyAdvance - 1.4, 0.16], [lx + 0.7, dyAdvance, 0.16], [lx, dyAdvance + 1.4, 0.16], [0, 0, 1], whitePaint);
          }
          // 직진 화살표 (정지선 전방 8m)
          const dyArrow = cy + sgn * 24;
          for (const lx of [cx - 7.7, cx + 7.7]) {
            mesh.addBox(lx - 0.15, dyArrow - 1.5, 0.16, 0.3, 3.0, 0.02, whitePaint);
            mesh.addQuad([lx - 0.8, dyArrow + sgn * 1.5, 0.16], [lx + 0.8, dyArrow + sgn * 1.5, 0.16], [lx, dyArrow + sgn * 3.0, 0.16], [lx, dyArrow + sgn * 3.0, 0.16], [0, 0, 1], whitePaint);
          }
        }
      }

      // 5) 중앙분리대 화단 조경 (Median Greenery Strip - 정류장 미설치 구간)
      const medianHedge = [0.22, 0.55, 0.28];
      const medianCurb = [0.75, 0.78, 0.82];
      for (const myBlock of [[480, 775], [1225, 1520]]) {
        const y0 = myBlock[0], y1 = myBlock[1];
        mesh.addBox(cx - 0.45, y0, 0.15, 0.9, y1 - y0, 0.25, medianCurb);
        mesh.addBox(cx - 0.35, y0, 0.40, 0.7, y1 - y0, 0.45, medianHedge);
        // 중앙 분리대 슬림 가로등 (48m 간격)
        for (let ly = y0 + 24; ly < y1 - 20; ly += 48) {
          mesh.addPillar(cx, ly, 0.4, 8.5, 0.16, [0.88, 0.90, 0.94]);
          mesh.addBox(cx - 1.2, ly - 0.12, 8.2, 2.4, 0.24, 0.22, [0.95, 0.95, 0.98, 1.4]);
        }
      }

      // =================================================================
      // [B] 중앙 BRT 입체 승강장 2개소 (수변공원 남측 Y=860 & 북측 Y=1140)
      // =================================================================
      const stationYs = [860, 1140];
      for (const sy of stationYs) {
        const pLen = 38, pWid = 4.8, pH = 0.45;
        // 1) 승강장 화강석 연석 플랫폼
        mesh.addBox(cx - pWid * 0.5, sy - pLen * 0.5, 0.15, pWid, pLen, pH, [0.74, 0.76, 0.80], [0.82, 0.84, 0.88]);

        // 2) 가장자리 노란색 시각장애인 안전 점자블록 띠
        const yelBrd = [0.95, 0.82, 0.15];
        mesh.addQuad([cx - pWid * 0.5, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx - pWid * 0.5 + 0.38, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx - pWid * 0.5 + 0.38, sy + pLen * 0.5, 0.15 + pH + 0.02], [cx - pWid * 0.5, sy + pLen * 0.5, 0.15 + pH + 0.02], [0, 0, 1], yelBrd);
        mesh.addQuad([cx + pWid * 0.5 - 0.38, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx + pWid * 0.5, sy - pLen * 0.5, 0.15 + pH + 0.02], [cx + pWid * 0.5, sy + pLen * 0.5, 0.15 + pH + 0.02], [cx + pWid * 0.5 - 0.38, sy + pLen * 0.5, 0.15 + pH + 0.02], [0, 0, 1], yelBrd);

        // 3) 미래형 유선형 글래스 캐노피 (Aerofoil Glass Shelter)
        const canW = 5.8, canL = 30, canH = 4.2;
        mesh.addCurvedVault(cx - canW * 0.5, sy - canL * 0.5, 0.15 + pH + 2.8, canW, canL, 1.3, [0.35, 0.70, 0.96, 1.45]);
        mesh.addBox(cx - canW * 0.5, sy - canL * 0.5, 0.15 + pH + 2.7, canW, canL, 0.15, [0.88, 0.90, 0.94]);

        // 4) 스테인리스 원형 기둥 6기
        for (const py of [sy - 12, sy - 5.0, sy, sy + 5.0, sy + 12]) {
          mesh.addPillar(cx, py, 0.15 + pH, 0.15 + pH + 3.0, 0.26, [0.92, 0.94, 0.96]);
        }

        // 5) 승강장 내부 벤치 및 BIT(버스정보단말기) & 스크린도어 가이드
        mesh.addBox(cx - 0.45, sy - 6.0, 0.15 + pH, 0.9, 4.0, 0.55, [0.35, 0.38, 0.42]);
        mesh.addBox(cx - 0.45, sy + 2.0, 0.15 + pH, 0.9, 4.0, 0.55, [0.35, 0.38, 0.42]);
        mesh.addBox(cx - 0.15, sy - 13.0, 0.15 + pH + 1.8, 0.3, 1.8, 0.9, [0.15, 0.18, 0.22], [0.20, 0.75, 0.95, 1.4]);
        mesh.addBox(cx - 0.15, sy + 13.0, 0.15 + pH + 1.8, 0.3, 1.8, 0.9, [0.15, 0.18, 0.22], [0.20, 0.75, 0.95, 1.4]);

        // 승강장 안전 난간 (글래스 펜스)
        mesh.addBox(cx - pWid * 0.5, sy - pLen * 0.35, 0.15 + pH, 0.08, pLen * 0.7, 1.1, [0.90, 0.94, 0.98, 1.25]);
        mesh.addBox(cx + pWid * 0.5 - 0.08, sy - pLen * 0.35, 0.15 + pH, 0.08, pLen * 0.7, 1.1, [0.90, 0.94, 0.98, 1.25]);

        // 6) 정류장 진입 보행 슬로프 램프 (양방향 완만한 경사)
        mesh.addQuad([cx - pWid * 0.5, sy - pLen * 0.5 - 4.5, 0.15], [cx + pWid * 0.5, sy - pLen * 0.5 - 4.5, 0.15], [cx + pWid * 0.5, sy - pLen * 0.5, 0.15 + pH], [cx - pWid * 0.5, sy - pLen * 0.5, 0.15 + pH], [0, -1, 1], [0.72, 0.74, 0.78]);
        mesh.addQuad([cx - pWid * 0.5, sy + pLen * 0.5, 0.15 + pH], [cx + pWid * 0.5, sy + pLen * 0.5, 0.15 + pH], [cx + pWid * 0.5, sy + pLen * 0.5 + 4.5, 0.15], [cx - pWid * 0.5, sy + pLen * 0.5 + 4.5, 0.15], [0, 1, 1], [0.72, 0.74, 0.78]);

        // [신규 4] 공공 스마트 자전거 대여소 (따릉이/스마트 모빌리티 스테이션)
        const bikeX = cx - 18.5, bikeY = sy - 18;
        mesh.addBox(bikeX - 6.0, bikeY - 2.0, 0.22, 12.0, 4.0, 0.06, [0.22, 0.24, 0.26]);
        mesh.addBox(bikeX - 5.5, bikeY - 0.15, 0.28, 11.0, 0.3, 0.65, [0.85, 0.88, 0.92]);
        for (let bk = 0; bk < 4; bk++) {
          const bx = bikeX - 4.2 + bk * 2.8;
          mesh.addBox(bx - 0.15, bikeY - 0.9, 0.28, 0.3, 1.8, 0.95, [0.96, 0.98, 1.0], [0.15, 0.68, 0.35]);
        }
      }

      // =================================================================
      // [C] 수변 신호 교차로 2개소 (Y=800 & Y=1200) - 도류화 교통섬, 횡단보도, 신호기
      // =================================================================
      const crossYs = [800, 1200];
      for (const cy of crossYs) {
        // 1) 남북 간선대로 횡단보도 (동서 횡단: 북측 cy + 14, 남측 cy - 14)
        const crossW = 5.2, stripeW = 0.55, stripeGap = 0.55;
        for (const dy of [-14.0, 14.0]) {
          for (let sx = cx - 11.5; sx <= cx + 11.5; sx += (stripeW + stripeGap)) {
            mesh.addQuad([sx, cy + dy - crossW * 0.5, 0.16], [sx + stripeW, cy + dy - crossW * 0.5, 0.16], [sx + stripeW, cy + dy + crossW * 0.5, 0.16], [sx, cy + dy + crossW * 0.5, 0.16], [0, 0, 1], whitePaint);
          }
        }

        // 2) 동서 간선도로 횡단보도 (남북 횡단: 서측 cx - 14, 동측 cx + 14)
        for (const dx of [-14.0, 14.0]) {
          for (let sy = cy - 11.5; sy <= cy + 11.5; sy += (stripeW + stripeGap)) {
            mesh.addQuad([cx + dx - crossW * 0.5, sy, 0.16], [cx + dx + crossW * 0.5, sy, 0.16], [cx + dx + crossW * 0.5, sy + stripeW, 0.16], [cx + dx - crossW * 0.5, sy + stripeW, 0.16], [0, 0, 1], whitePaint);
          }
        }

        // 3) 남북 및 동서 방향 백색 정지선
        for (const sgn of [-1, 1]) {
          const sy = cy + sgn * 17.2;
          mesh.addQuad([cx - 12.0, sy - 0.28, 0.17], [cx - 3.4, sy - 0.28, 0.17], [cx - 3.4, sy + 0.28, 0.17], [cx - 12.0, sy + 0.28, 0.17], [0, 0, 1], whitePaint);
          mesh.addQuad([cx + 3.4, sy - 0.28, 0.17], [cx + 12.0, sy - 0.28, 0.17], [cx + 12.0, sy + 0.28, 0.17], [cx + 3.4, sy + 0.28, 0.17], [0, 0, 1], whitePaint);

          const sx = cx + sgn * 17.2;
          mesh.addQuad([sx - 0.28, cy - 12.0, 0.17], [sx + 0.28, cy - 12.0, 0.17], [sx + 0.28, cy - 3.4, 0.17], [sx - 0.28, cy - 3.4, 0.17], [0, 0, 1], whitePaint);
          mesh.addQuad([sx - 0.28, cy + 3.4, 0.17], [sx + 0.28, cy + 3.4, 0.17], [sx + 0.28, cy + 12.0, 0.17], [sx - 0.28, cy + 12.0, 0.17], [0, 0, 1], whitePaint);
        }

        // 4) 4개 모퉁이 우회전 도류화 삼각 교통섬 (Corner Islands)
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) {
            const ix = cx + sx * 16.5;
            const iy = cy + sy * 16.5;
            mesh.addBox(ix - 1.8, iy - 1.8, 0.05, 3.6, 3.6, 0.25, [0.72, 0.75, 0.78]);
            mesh.addBox(ix - 1.4, iy - 1.4, 0.30, 2.8, 2.8, 0.35, [0.22, 0.58, 0.28]); // 미니 관목
          }
        }

        // 5) 보행자 안전 보호 볼라드 (Bollards 8기)
        for (const dy of [-17.2, 17.2]) {
          for (const bx of [cx - 12.5, cx + 12.5]) {
            mesh.addPillar(bx, cy + dy, 0.2, 1.0, 0.12, [0.88, 0.90, 0.94]);
          }
        }

        // 6) 교차로 L자형 신호등 철골 기둥 & 하우징
        // 서남 모퉁이 (cx - 14.5, cy - 14.5)
        mesh.addPillar(cx - 14.5, cy - 14.5, 0.15, 7.8, 0.24, [0.22, 0.24, 0.28]);
        mesh.addBox(cx - 14.5, cy - 14.65, 7.5, 9.0, 0.32, 0.32, [0.22, 0.24, 0.28]); // 남북용 암
        mesh.addBox(cx - 6.2, cy - 14.9, 7.05, 1.4, 0.45, 0.6, [0.12, 0.12, 0.14]);   // 남북용 하우징
        mesh.addBox(cx - 14.65, cy - 14.5, 7.5, 0.32, 9.0, 0.32, [0.22, 0.24, 0.28]); // 동서용 암
        mesh.addBox(cx - 14.9, cy - 6.2, 7.05, 0.45, 1.4, 0.6, [0.12, 0.12, 0.14]);   // 동서용 하우징

        // 동북 모퉁이 (cx + 14.5, cy + 14.5)
        mesh.addPillar(cx + 14.5, cy + 14.5, 0.15, 7.8, 0.24, [0.22, 0.24, 0.28]);
        mesh.addBox(cx + 5.5, cy + 14.35, 7.5, 9.0, 0.32, 0.32, [0.22, 0.24, 0.28]);  // 남북용 암
        mesh.addBox(cx + 4.8, cy + 14.45, 7.05, 1.4, 0.45, 0.6, [0.12, 0.12, 0.14]);  // 남북용 하우징
        mesh.addBox(cx + 14.35, cy + 5.5, 7.5, 0.32, 9.0, 0.32, [0.22, 0.24, 0.28]);  // 동서용 암
        mesh.addBox(cx + 14.45, cy + 4.8, 7.05, 0.45, 1.4, 0.6, [0.12, 0.12, 0.14]);  // 동서용 하우징

        // [신규 5] 횡단보도 보행자 안전 노란색 점자블록 띠 (Tactile Paving)
        for (const dy of [-16.8, 16.8]) {
          for (const sgn of [-1, 1]) {
            const bx = cx + sgn * 7.5;
            mesh.addQuad([bx - 1.4, cy + dy - 0.7, 0.23], [bx + 1.4, cy + dy - 0.7, 0.23], [bx + 1.4, cy + dy + 0.7, 0.23], [bx - 1.4, cy + dy + 0.7, 0.23], [0, 0, 1], [0.96, 0.82, 0.15]);
          }
        }
        // 신호등 기둥 상단 보행자 안전 점멸 경보등
        mesh.addBox(cx - 14.65, cy - 14.65, 8.1, 0.3, 0.3, 0.35, [0.98, 0.85, 0.15, 2.2]);
        mesh.addBox(cx + 14.35, cy + 14.35, 8.1, 0.3, 0.3, 0.35, [0.98, 0.85, 0.15, 2.2]);
      }

      // =================================================================
      // [D] 대형 수변 횡단 교량 (Grand Waterfront Bridge Y=944 ~ 1104)
      // =================================================================
      const bY0 = 944, bY1 = 1104, bLen = bY1 - bY0;
      // 1) 교량 콘크리트 슬래브 (폭 29m, 두께 2.2m)
      mesh.addBox(cx - 14.5, bY0, -1.8, 29.0, bLen, 2.0, [0.55, 0.58, 0.62], [0.68, 0.70, 0.74]);

      // 2) 캔틸레버 돌출 광폭 수변 보행 전망 데크 (폭 3.2m, 양측)
      mesh.addBox(cx - 17.7, bY0, 0.10, 3.2, bLen, 0.25, [0.82, 0.84, 0.88]); // 서측 보행 데크
      mesh.addBox(cx + 14.5, bY0, 0.10, 3.2, bLen, 0.25, [0.82, 0.84, 0.88]); // 동측 보행 데크

      // 교량 중앙(Y = 1024) 반원형 돌출 전망 발코니 2개소 + 전망 벤치
      const midY = (bY0 + bY1) * 0.5;
      mesh.addBox(cx - 20.5, midY - 6.0, 0.10, 3.2, 12.0, 0.25, [0.84, 0.86, 0.90]);
      mesh.addBox(cx + 17.3, midY - 6.0, 0.10, 3.2, 12.0, 0.25, [0.84, 0.86, 0.90]);
      // 전망 벤치
      mesh.addBox(cx - 19.8, midY - 2.5, 0.35, 1.2, 5.0, 0.5, [0.42, 0.30, 0.22]);
      mesh.addBox(cx + 18.6, midY - 2.5, 0.35, 1.2, 5.0, 0.5, [0.42, 0.30, 0.22]);

      // 3) 교량 외곽 안전 방호벽 및 화이트 난간 (White Bridge Railings)
      const railH = 1.35;
      mesh.addBox(cx - 17.8, bY0, 0.3, 0.25, bLen, railH, [0.95, 0.96, 0.98]);
      mesh.addBox(cx - 17.9, bY0, 0.3 + railH - 0.12, 0.45, bLen, 0.12, [0.88, 0.90, 0.94]);
      mesh.addBox(cx + 17.55, bY0, 0.3, 0.25, bLen, railH, [0.95, 0.96, 0.98]);
      mesh.addBox(cx + 17.45, bY0, 0.3 + railH - 0.12, 0.45, bLen, 0.12, [0.88, 0.90, 0.94]);

      // 차도-보도 분리 방호벽
      mesh.addBox(cx - 14.5, bY0, 0.2, 0.35, bLen, 0.65, [0.70, 0.72, 0.76]);
      mesh.addBox(cx + 14.15, bY0, 0.2, 0.35, bLen, 0.65, [0.70, 0.72, 0.76]);

      // 4) 교량 하부 거대한 타원형 콘크리트 교각 6기
      for (const pierY of [bY0 + 35, bY0 + 80, bY0 + 125]) {
        mesh.addPillar(cx - 7.5, pierY, -3.0, -0.2, 2.4, [0.62, 0.65, 0.68], 12);
        mesh.addPillar(cx + 7.5, pierY, -3.0, -0.2, 2.4, [0.62, 0.65, 0.68], 12);
        mesh.addBox(cx - 10.0, pierY - 2.5, -0.6, 20.0, 5.0, 0.8, [0.58, 0.60, 0.64]);
      }

      // 5) 교량 상부 대형 화이트 아치 리브 & 서스펜션 케이블 (Tied-Arch Ribs)
      const archH = 26;
      mesh.addCurvedVaultY(cx - 14.8, bY0, 0.3, 1.4, bLen, archH, [0.96, 0.97, 0.99]);
      mesh.addCurvedVaultY(cx + 13.4, bY0, 0.3, 1.4, bLen, archH, [0.96, 0.97, 0.99]);

      // 횡방향 윈드 브레이싱 크로스빔 4개소 (Wind Bracing Cross-beams)
      for (const f of [0.30, 0.43, 0.57, 0.70]) {
        const by = bY0 + bLen * f;
        const bz = 0.3 + Math.sin(f * Math.PI) * archH;
        mesh.addBox(cx - 14.0, by - 0.4, bz, 28.0, 0.8, 0.8, [0.92, 0.94, 0.98]);
      }

      // 수직 서스펜션 케이블 8쌍
      for (let cy = bY0 + 18; cy < bY1 - 18; cy += 16) {
        const u = (cy - bY0) / bLen;
        const curArchZ = 0.3 + Math.sin(u * Math.PI) * archH;
        mesh.addPillar(cx - 14.0, cy, 0.3, curArchZ, 0.14, [0.88, 0.90, 0.95]);
        mesh.addPillar(cx + 14.0, cy, 0.3, curArchZ, 0.14, [0.88, 0.90, 0.95]);
      }

      // 교량 위 슬림 가로등 8기
      for (let cy = bY0 + 20; cy < bY1 - 20; cy += 32) {
        mesh.addPillar(cx - 14.3, cy, 0.65, 8.2, 0.16, [0.90, 0.92, 0.96]);
        mesh.addBox(cx - 14.3, cy - 0.15, 7.9, 1.8, 0.3, 0.25, [0.95, 0.95, 0.98, 1.4]);
        mesh.addPillar(cx + 14.3, cy, 0.65, 8.2, 0.16, [0.90, 0.92, 0.96]);
        mesh.addBox(cx + 12.5, cy - 0.15, 7.9, 1.8, 0.3, 0.25, [0.95, 0.95, 0.98, 1.4]);
      }

      // =================================================================
      // [E] 하천 둔치 친수공간 및 입체 수변 산책로 (Riverbank Linear Park)
      // =================================================================
      // 대교 아래(Z = 0.12m)를 통과하는 남북 하천 둔치 산책로 & 자전거도로
      for (const rSide of [bY0 - 18, bY1 + 10]) {
        // 목재 수변 데크 산책로 (폭 5m, X = cx - 140 ~ cx + 140)
        mesh.addBox(cx - 140, rSide, 0.08, 280, 5.0, 0.16, [0.68, 0.58, 0.48]);
        // 와인레드 우레탄 자전거 도로 (폭 3.2m)
        mesh.addBox(cx - 140, rSide + 5.5, 0.08, 280, 3.2, 0.16, [0.62, 0.20, 0.25]);

        // 물가 친수 계단 스탠드 (Amphitheater Steps 3단)
        const stepDir = (rSide < 1000) ? 1 : -1;
        mesh.addBox(cx - 60, rSide - stepDir * 2.5, 0.04, 120, 2.5, 0.14, [0.82, 0.84, 0.88]);
        mesh.addBox(cx - 50, rSide - stepDir * 5.0, -0.05, 100, 2.5, 0.14, [0.78, 0.80, 0.84]);

        // 수변 조경수 (수양버들 및 메타세콰이어)
        for (let tx = cx - 120; tx <= cx + 120; tx += 36) {
          if (Math.abs(tx - cx) < 22) continue; // 교량 바로 밑 제외
          mesh.addTree(tx, rSide + 12.0, 0.1, 14, 5.8, 'deciduous');
        }
      }

      // 교량 보도에서 수변 산책로로 이어지는 연결 보행 경사로 (Connecting Ramps)
      mesh.addQuad([cx - 17.5, bY0, 0.25], [cx - 14.5, bY0, 0.25], [cx - 24.0, bY0 - 16, 0.12], [cx - 27.0, bY0 - 16, 0.12], [0, -1, 1], [0.78, 0.80, 0.84]);
      mesh.addQuad([cx + 14.5, bY0, 0.25], [cx + 17.5, bY0, 0.25], [cx + 27.0, bY0 - 16, 0.12], [cx + 24.0, bY0 - 16, 0.12], [0, -1, 1], [0.78, 0.80, 0.84]);
      mesh.addQuad([cx - 17.5, bY1, 0.25], [cx - 14.5, bY1, 0.25], [cx - 24.0, bY1 + 16, 0.12], [cx - 27.0, bY1 + 16, 0.12], [0, 1, 1], [0.78, 0.80, 0.84]);
      mesh.addQuad([cx + 14.5, bY1, 0.25], [cx + 17.5, bY1, 0.25], [cx + 27.0, bY1 + 16, 0.12], [cx + 24.0, bY1 + 16, 0.12], [0, 1, 1], [0.78, 0.80, 0.84]);

      // =================================================================
      // [F] 보도(인도), 가로등, 느티나무 가로수 & 스트리트 퍼니처
      // =================================================================
      const swColor = [0.82, 0.84, 0.88];
      const curbColor = [0.68, 0.70, 0.74];
      const yBlocks = [[480, 778], [822, 944], [1104, 1178], [1222, 1520]];
      for (const yBlock of yBlocks) {
        const y0 = yBlock[0], y1 = yBlock[1];
        // 서측 보도 (폭 4.5m, 높이 0.22m)
        mesh.addBox(cx - 16.5, y0, 0.05, 4.5, y1 - y0, 0.22, swColor);
        mesh.addBox(cx - 12.35, y0, 0.05, 0.35, y1 - y0, 0.26, curbColor);

        // 동측 보도 (폭 4.5m, 높이 0.22m)
        mesh.addBox(cx + 12.0, y0, 0.05, 4.5, y1 - y0, 0.22, swColor);
        mesh.addBox(cx + 12.0, y0, 0.05, 0.35, y1 - y0, 0.26, curbColor);

        // 인도 위 가로등, 가로수, 수목보호대 및 벤치
        for (let ly = y0 + 12; ly < y1 - 12; ly += 32) {
          // 서측 가로등 & 가로수
          mesh.addPillar(cx - 14.5, ly, 0.27, 9.2, 0.18, [0.85, 0.88, 0.92]);
          mesh.addBox(cx - 14.5, ly - 0.15, 8.9, 1.8, 0.3, 0.25, [0.95, 0.95, 0.98, 1.3]);
          mesh.addTree(cx - 18.2, ly + 16, 0.1, 13, 5.4, 'deciduous');
          // 가로수 수목보호대 (다크 메탈 그레이팅)
          mesh.addBox(cx - 19.4, ly + 14.8, 0.08, 2.4, 2.4, 0.04, [0.22, 0.24, 0.26]);

          // 동측 가로등 & 가로수
          mesh.addPillar(cx + 14.5, ly, 0.27, 9.2, 0.18, [0.85, 0.88, 0.92]);
          mesh.addBox(cx + 12.7, ly - 0.15, 8.9, 1.8, 0.3, 0.25, [0.95, 0.95, 0.98, 1.3]);
          mesh.addTree(cx + 18.2, ly + 16, 0.1, 13, 5.4, 'deciduous');
          mesh.addBox(cx + 17.0, ly + 14.8, 0.08, 2.4, 2.4, 0.04, [0.22, 0.24, 0.26]);

          // 인도 위 보행자 목재 벤치
          if (ly % 64 === 0) {
            mesh.addBox(cx - 15.6, ly + 8, 0.27, 1.2, 3.2, 0.48, [0.42, 0.32, 0.24]);
            mesh.addBox(cx + 14.4, ly + 8, 0.27, 1.2, 3.2, 0.48, [0.42, 0.32, 0.24]);
          }
        }
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

    // 5. 사용자 조감도에 맞춘 초고품질 3D 건축 에셋 빌더 (발자국 충돌 방지 시스템 연동)
    buildHighQualityBuildings(mesh) {
      const sim = this.sim;
      const blocks = sim.zoneBlocks || [];
      const fp = new FootprintManager();
      this.footprintManager = fp;

      // 5-0. 충돌 방지 금지 구역(도로, 하천, 회전교차로) 선행 등록
      // 1) 도로망 (도로 폭 + 보도/완충 이격거리 4.5m 반경 박스 샘플링)
      if (sim.roads && sim.nodes) {
        const nodeMap = new Map();
        for (const n of sim.nodes) nodeMap.set(n.id, n);

        for (const r of sim.roads) {
          const fn = nodeMap.get(r.from);
          const tn = nodeMap.get(r.to);
          if (!fn || !tn) continue;

          const width = r.type === 'highway' ? 24 : (r.type === 'arterial' ? 16 : (r.type === 'parkway' ? 6 : 11));
          const clearRadius = width * 0.5 + 4.5;
          const roadLen = Math.hypot(tn.x - fn.x, tn.y - fn.y);
          const steps = Math.max(2, Math.ceil(roadLen / 10));

          for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            let px, py;
            if (r.midPoint) {
              const u = 1 - t;
              px = u * u * fn.x + 2 * u * t * r.midPoint.x + t * t * tn.x;
              py = u * u * fn.y + 2 * u * t * r.midPoint.y + t * t * tn.y;
            } else {
              px = fn.x + (tn.x - fn.x) * t;
              py = fn.y + (tn.y - fn.y) * t;
            }
            fp.addBox(px - clearRadius, py - clearRadius, px + clearRadius, py + clearRadius, 'road', { roadId: r.id });
          }
        }
      }

      // 2) 중앙 BRT 주간선대로 및 보도 코리더 (X = 1200 중심 ± 20m)
      fp.addBox(1200 - 20, 450, 1200 + 20, 1550, 'road', { name: 'BRT대로' });

      // 3) 생태 하천 및 수변공원 보행/자전거 축 (Y = 880 ~ 1165 전 구간 건축 금지)
      fp.addBox(-500, 880, 3200, 1165, 'river', { name: '하천축' });

      // 4) 원형 회전교차로 교통섬 및 주변 완충구역
      let rbs = sim.roundabouts ? [...sim.roundabouts] : [];
      for (const rb of rbs) {
        const rad = (rb.radius || 24) + 6;
        fp.addBox(rb.x - rad, rb.y - rad, rb.x + rad, rb.y + rad, 'roundabout');
      }

      // 5-1. 특수 랜드마크 (초등학교와 운동장, 대형 복합환승센터)
      for (const b of blocks) {
        // [A] 초등학교와 규격 운동장 (초품아 캠퍼스)
        if (b.landUse === 'school') {
          fp.addBox(b.x - 2, b.y - 2, b.x + b.w + 2, b.y + b.h + 2, 'school');

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
          fp.addBox(b.x - 55, b.y - 2, b.x + transW + 30, b.y + b.h + 2, 'transit');

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

      // 5-2. 주거 슈퍼블록, 중심상업, 테크노밸리 건축 에셋 초고화질 배치 (현실적 비례·재질·창문·야외공간 & AABB 충돌 방지 보장)
      if (!sim.zoneCells) return;

      for (const cell of sim.zoneCells.values()) {
        if (!cell.type) continue;
        if (cell.landUse === 'school' || cell.landUse === 'transit' || cell.landUse === 'river') continue;

        // 1) 한국형 고품격 아파트 대단지 (4대 특화 모델: 와이드 판상형, 테라스형, 파노라마 타워, 트윈 스카이브릿지)
        if (cell.type === 'residential') {
          if (cell.x % 48 === 0 && cell.y % 48 === 0) {
            const modelType = Math.abs(Math.floor(cell.x / 48) + Math.floor(cell.y / 48)) % 4;
            let aptW, aptD;
            if (modelType === 0) { aptW = 54; aptD = 18; }
            else if (modelType === 1) { aptW = 50; aptD = 18; }
            else if (modelType === 2) { aptW = 34; aptD = 34; }
            else { aptW = 44; aptD = 22; }

            // 발자국 이격거리 검사 (인동 간격 6.0m 엄격 보장)
            if (fp.isOverlapping(cell.x, cell.y, cell.x + aptW, cell.y + aptD, 6.0)) {
              continue; // 겹침 발생 시 배치 건너뜀
            }
            fp.addBox(cell.x, cell.y, cell.x + aptW, cell.y + aptD, 'building_residential', { modelType });

            // [Residential Model 0] 4-Bay 럭셔리 와이드 판상형 (화강석 3단 기단부, 베이지/브론즈 세라믹, 옥탑 윙 & 문주/피트니스 야외공간)
            if (modelType === 0) {
              const stories = 20 + ((cell.x * 3 + cell.y * 7) % 6);
              const height = stories * 3.2; // 64m ~ 80m
              const pilotiH = 4.8;

              // [1] 저층 1~2층 다크 차콜 천연 화강석 기단부 및 필로티
              for (let px = cell.x + 4; px <= cell.x + aptW - 4; px += 9.2) {
                mesh.addPillar(px, cell.y + 3.2, 0, pilotiH, 0.90, [0.26, 0.28, 0.32]);
                mesh.addPillar(px, cell.y + aptD - 3.2, 0, pilotiH, 0.90, [0.26, 0.28, 0.32]);
              }
              // 통유리 로비 & 호텔식 드롭오프 회전문
              mesh.addBox(cell.x + 14, cell.y + 3.5, 0, 26, aptD - 7.0, pilotiH, [0.22, 0.50, 0.75, 1.35]);
              // 그랜드 문주(Portico) 캐노피 및 브론즈 처마
              mesh.addBox(cell.x + 16, cell.y + 0.8, 0, 22, 3.8, 4.4, [0.28, 0.26, 0.24]);
              mesh.addBox(cell.x + 15, cell.y + 0.5, 4.4, 24, 4.4, 0.35, [0.72, 0.48, 0.25]); // 브론즈 처마

              // [2] 주거 본동 매스 (크림 아이보리 세라믹 패널 + 웜그레이)
              mesh.addBox(cell.x + 1.2, cell.y + 1.2, pilotiH, aptW - 2.4, aptD - 2.4, height - pilotiH, [0.94, 0.93, 0.91]);

              // 듀얼 EV/계단실 코어 분절 채널 (모던 다크 차콜)
              mesh.addBox(cell.x + 15.5, cell.y + 0.6, pilotiH, 5.5, aptD - 1.2, height - 1.5, [0.24, 0.26, 0.30]);
              mesh.addBox(cell.x + 33.0, cell.y + 0.6, pilotiH, 5.5, aptD - 1.2, height - 1.5, [0.24, 0.26, 0.30]);

              // 4-Bay 개별 세대 발코니 창호 & 틴티드 글래스 난간 & 실외기실 루버
              for (let fz = pilotiH + 2.0; fz < height - 5; fz += 6.4) {
                // 발코니 창호 프레임 & 글래스
                mesh.addBox(cell.x + 2.5, cell.y + 0.5, fz, 11.5, 1.2, 2.5, [0.18, 0.48, 0.72, 1.35]);
                mesh.addBox(cell.x + 22.5, cell.y + 0.5, fz, 9.0, 1.2, 2.5, [0.18, 0.48, 0.72, 1.35]);
                mesh.addBox(cell.x + 39.5, cell.y + 0.5, fz, 12.0, 1.2, 2.5, [0.18, 0.48, 0.72, 1.35]);

                // 투명 글래스 난간대 (하부 0.9m)
                mesh.addBox(cell.x + 2.5, cell.y + 0.2, fz, 11.5, 0.3, 0.9, [0.82, 0.92, 0.98, 1.25]);
                mesh.addBox(cell.x + 22.5, cell.y + 0.2, fz, 9.0, 0.3, 0.9, [0.82, 0.92, 0.98, 1.25]);
                mesh.addBox(cell.x + 39.5, cell.y + 0.2, fz, 12.0, 0.3, 0.9, [0.82, 0.92, 0.98, 1.25]);

                // 실외기실 환기 루버 그릴 (다크 그레이)
                mesh.addBox(cell.x + 14.2, cell.y + 0.5, fz + 0.4, 1.2, 0.8, 1.6, [0.35, 0.38, 0.42]);
                mesh.addBox(cell.x + 38.2, cell.y + 0.5, fz + 0.4, 1.2, 0.8, 1.6, [0.35, 0.38, 0.42]);
              }

              // 브론즈 테라코타 수평 띠장
              mesh.addBox(cell.x + 1.0, cell.y + 1.0, height - 4.5, aptW - 2.0, aptD - 2.0, 1.8, [0.75, 0.42, 0.22]);

              // 옥상 윙 루프탑 장식 + 조명 엠블럼 박스 + 태양광 BIPV
              mesh.addBox(cell.x + 14, cell.y + 3.5, height, 26, aptD - 7, 4.8, [0.55, 0.58, 0.65]);
              mesh.addBox(cell.x + 11, cell.y + 2.5, height + 4.8, 32, aptD - 5, 0.6, [0.88, 0.90, 0.95]);
              mesh.addBox(cell.x + 18, cell.y + 4.5, height + 5.4, 18, aptD - 9, 0.4, [0.12, 0.18, 0.35]); // BIPV
              // 브랜드 엠블럼 라이트박스
              mesh.addBox(cell.x + 21, cell.y + 1.0, height + 1.2, 12, 1.0, 2.4, [0.98, 0.78, 0.25, 1.6]);

              // [3] 단지 내 야외 공간 (보도블록 산책로, 조경 소나무 군락, 야외 운동기구, 자전거 보관소)
              mesh.addBox(cell.x - 2, cell.y + 2, 0.05, 5, aptD - 4, 0.06, [0.78, 0.76, 0.72]); // 보도블록
              mesh.addTree(cell.x + 5, cell.y + 7, 0.1, 11, 4.0, 'pine');
              mesh.addTree(cell.x + aptW - 6, cell.y + 7, 0.1, 10, 3.8, 'pine');
              // 야외 피트니스 운동기구 (트윈 머신 모형)
              mesh.addBox(cell.x + 8, cell.y + 2.5, 0.1, 3.2, 2.2, 1.5, [0.22, 0.52, 0.82]);
              // 자전거 보관소 쉘터
              mesh.addBox(cell.x + aptW - 12, cell.y + 2.2, 0.1, 5.5, 2.4, 2.4, [0.38, 0.42, 0.48]);
            }

            // [Residential Model 1] 계단식 테라스 단차 판상형 (목재 데크, 안전 유리난간, 플랜터 화단 & 모험 놀이터)
            else if (modelType === 1) {
              const stories = 18 + ((cell.x + cell.y) % 5);
              const height = stories * 3.2; // 57m ~ 70m
              const pilotiH = 4.8;
              const midH = Math.min(height - 12, 44.8);

              // 1~14층 본체 매스 (50m x 18m)
              mesh.addBox(cell.x + 1.2, cell.y + 1.2, 0, aptW - 2.4, aptD - 2.4, midH, [0.91, 0.92, 0.94]);

              // 15~18층: 좌우 6m 셋백 (폭 38m)
              if (height > midH) {
                mesh.addBox(cell.x + 6, cell.y + 1.5, midH, aptW - 12, aptD - 3.0, height - midH, [0.93, 0.94, 0.96]);

                // 하부 옥상 계단식 테라스 정원 (목재 데크 + 식재 플랜터 + 유리난간 + 티테이블 파라솔)
                mesh.addBox(cell.x + 1.5, cell.y + 1.5, midH, 4.5, aptD - 3.0, 0.25, [0.65, 0.52, 0.40]);
                mesh.addBox(cell.x + aptW - 6.0, cell.y + 1.5, midH, 4.5, aptD - 3.0, 0.25, [0.65, 0.52, 0.40]);
                // 유리 안전 난간
                mesh.addBox(cell.x + 1.5, cell.y + 1.5, midH + 0.25, 4.5, 0.2, 1.1, [0.85, 0.92, 0.98, 1.25]);
                mesh.addBox(cell.x + aptW - 6.0, cell.y + 1.5, midH + 0.25, 4.5, 0.2, 1.1, [0.85, 0.92, 0.98, 1.25]);
                // 식재 플랜터 관목
                mesh.addBox(cell.x + 2.0, cell.y + 2.2, midH + 0.25, 3.5, aptD - 4.4, 0.5, [0.28, 0.65, 0.32]);
                mesh.addBox(cell.x + aptW - 5.5, cell.y + 2.2, midH + 0.25, 3.5, aptD - 4.4, 0.5, [0.28, 0.65, 0.32]);
                // 테라스 파라솔 세트
                mesh.addBox(cell.x + 3.2, cell.y + 5.5, midH + 0.25, 1.2, 1.2, 0.6, [0.95, 0.92, 0.88]);
                mesh.addBox(cell.x + 2.5, cell.y + 4.8, midH + 2.0, 2.6, 2.6, 0.25, [0.88, 0.42, 0.25]);
              }

              // 전면 글래스 창호 밴드
              for (let fz = pilotiH + 2.4; fz < height - 5; fz += 6.4) {
                mesh.addBox(cell.x + 7.5, cell.y + 0.5, fz, aptW - 15, 1.2, 2.4, [0.20, 0.48, 0.72, 1.35]);
              }

              // 옥탑 기계실
              mesh.addBox(cell.x + 16, cell.y + 4, height, 18, aptD - 8, 4.0, [0.62, 0.65, 0.72]);

              // 단지 내 어린이 모험 놀이터 (X: cell.x + 3, Y: cell.y + 2.5)
              mesh.addBox(cell.x + 2.5, cell.y + 2.5, 0.1, 13, 13, 0.08, [0.22, 0.52, 0.82]); // 블루 우레탄
              mesh.addBox(cell.x + 4.0, cell.y + 4.0, 0.18, 4.0, 4.0, 0.18, [0.95, 0.68, 0.18]); // 옐로우 탄성존
              mesh.addBox(cell.x + 5.0, cell.y + 5.0, 0.36, 2.6, 2.6, 3.4, [0.95, 0.28, 0.22]); // 놀이성 타워
              mesh.addBox(cell.x + 5.2, cell.y + 7.6, 0.36, 1.8, 3.2, 0.3, [0.96, 0.85, 0.18]); // 미끄럼틀
              // 그네 세트
              mesh.addBox(cell.x + 10.5, cell.y + 4.0, 0.18, 0.3, 4.5, 2.8, [0.25, 0.55, 0.85]);
              mesh.addBox(cell.x + 13.0, cell.y + 4.0, 0.18, 0.3, 4.5, 2.8, [0.25, 0.55, 0.85]);
              mesh.addBox(cell.x + 10.5, cell.y + 4.0, 2.9, 2.8, 0.3, 0.25, [0.95, 0.75, 0.20]);
              // 보호자 휴게 벤치
              mesh.addBox(cell.x + 3.0, cell.y + 11.5, 0.18, 3.2, 1.2, 0.45, [0.45, 0.32, 0.24]);
            }

            // [Residential Model 2] 십자형/Y형 파노라마 글래스 타워 (초고층 랜드마크, 커튼월 수직루버, 스카이라운지 & 썬큰 분수광장)
            else if (modelType === 2) {
              const stories = 32 + ((cell.x * 5 + cell.y * 11) % 8);
              const height = stories * 3.2; // 102m ~ 125m 초고층 랜드마크
              const pilotiH = 6.0;

              // 지상 1층 더블 하이트 그랜드 필로티 및 드롭오프 로비
              for (let cx = cell.x + 4; cx <= cell.x + aptW - 4; cx += 13) {
                for (let cy = cell.y + 4; cy <= cell.y + aptD - 4; cy += 13) {
                  mesh.addPillar(cx, cy, 0, pilotiH, 0.95, [0.35, 0.38, 0.42]);
                }
              }
              mesh.addBox(cell.x + 7, cell.y + 7, 0, aptW - 14, aptD - 14, pilotiH, [0.22, 0.55, 0.82, 1.35]);

              // 십자형(Cross) 타워 매스 본체 & 코어
              mesh.addBox(cell.x + 6, cell.y + 6, pilotiH, 22, 22, height - pilotiH, [0.28, 0.30, 0.35]);
              // 4방향 돌출 윙 매스
              mesh.addBox(cell.x + 6, cell.y + 1.2, pilotiH, 22, 5.0, height - pilotiH - 3, [0.93, 0.94, 0.96]);
              mesh.addBox(cell.x + 6, cell.y + aptD - 6.2, pilotiH, 22, 5.0, height - pilotiH - 3, [0.93, 0.94, 0.96]);
              mesh.addBox(cell.x + 1.2, cell.y + 6, pilotiH, 5.0, 22, height - pilotiH - 3, [0.93, 0.94, 0.96]);
              mesh.addBox(cell.x + aptW - 6.2, cell.y + 6, pilotiH, 5.0, 22, height - pilotiH - 3, [0.93, 0.94, 0.96]);

              // 4개 코너 대형 파노라마 커튼월 창호 & 수직 루버 핀
              for (let fz = pilotiH + 3.2; fz < height - 6; fz += 6.4) {
                mesh.addBox(cell.x + 6.8, cell.y + 0.6, fz, 20.4, 1.2, 2.8, [0.18, 0.58, 0.88, 1.45]);
                mesh.addBox(cell.x + 6.8, cell.y + aptD - 1.8, fz, 20.4, 1.2, 2.8, [0.18, 0.58, 0.88, 1.45]);
              }
              // 모서리 수직 알루미늄 루버 핀 (Spandrel Mullion)
              mesh.addBox(cell.x + 1.0, cell.y + 1.0, pilotiH, 0.6, 0.6, height - pilotiH, [0.95, 0.96, 0.98]);
              mesh.addBox(cell.x + aptW - 1.6, cell.y + 1.0, pilotiH, 0.6, 0.6, height - pilotiH, [0.95, 0.96, 0.98]);
              mesh.addBox(cell.x + 1.0, cell.y + aptD - 1.6, pilotiH, 0.6, 0.6, height - pilotiH, [0.95, 0.96, 0.98]);
              mesh.addBox(cell.x + aptW - 1.6, cell.y + aptD - 1.6, pilotiH, 0.6, 0.6, height - pilotiH, [0.95, 0.96, 0.98]);

              // 최상층 360도 스카이라운지 전망대 & 왕관형 루프탑 조명 핀
              mesh.addBox(cell.x + 4, cell.y + 4, height, aptW - 8, aptD - 8, 4.8, [0.20, 0.62, 0.94, 1.50]);
              mesh.addBox(cell.x + 7.5, cell.y + 7.5, height + 4.8, 19, 19, 0.7, [0.88, 0.28, 0.25]); // 헬리패드
              // 왕관형 크라운 조명 핀
              mesh.addBox(cell.x + 3.5, cell.y + 3.5, height + 4.8, aptW - 7, 0.5, 2.2, [0.95, 0.96, 0.98, 1.4]);
              mesh.addBox(cell.x + 3.5, cell.y + aptD - 4.0, height + 4.8, aptW - 7, 0.5, 2.2, [0.95, 0.96, 0.98, 1.4]);

              // 단지 내 유러피안 썬큰 분수광장 및 벚나무 산책로
              mesh.addCurbRing(cell.x + 8, cell.y + 8, 0.05, 0.45, 6.5, 1.4, [0.85, 0.88, 0.92], [0.18, 0.55, 0.85]);
              mesh.addPillar(cell.x + 8, cell.y + 8, 0.45, 2.5, 0.35, [0.92, 0.95, 0.98]); // 분수 노즐
              mesh.addTree(cell.x + aptW - 6, cell.y + 6, 0.1, 10, 3.8, 'cherry');
              mesh.addTree(cell.x + 6, cell.y + aptD - 6, 0.1, 10, 3.8, 'cherry');
            }

            // [Residential Model 3] 트윈 슬림 타워 & 더블덱 스카이브릿지 (트러스 하부구조, 코발트 블루 액센트, 배드민턴장 & 덩굴 파고라)
            else {
              const stories = 25 + ((cell.x + cell.y) % 7);
              const height = stories * 3.2; // 80m ~ 100m
              const pilotiH = 4.8;

              // 서측 슬림 타워 (17m x 20m) & 동측 슬림 타워 (17m x 20m)
              mesh.addBox(cell.x + 1.2, cell.y + 1.0, pilotiH, 17, 20, height - pilotiH, [0.93, 0.94, 0.96]);
              mesh.addBox(cell.x + 25.8, cell.y + 1.0, pilotiH, 17, 20, height - pilotiH, [0.93, 0.94, 0.96]);

              // 지상 1층 커뮤니티 피트니스/카페 로비 회랑
              mesh.addBox(cell.x + 17.5, cell.y + 3.5, 0, 9.0, 15, pilotiH, [0.25, 0.50, 0.75, 1.3]);

              // 지상 15~16층 높이 공중 글래스 스카이브릿지 (Double-deck Skybridge & Truss)
              const bridgeZ = Math.min(height - 15, 48.0);
              mesh.addBox(cell.x + 16, cell.y + 3.5, bridgeZ, 12, 15, 6.0, [0.85, 0.92, 0.98, 1.40]);
              // 스카이브릿지 하부 스틸 트러스 프레임
              mesh.addBox(cell.x + 16, cell.y + 4.0, bridgeZ - 1.2, 12, 1.2, 1.2, [0.32, 0.35, 0.40]);
              mesh.addBox(cell.x + 16, cell.y + 16.0, bridgeZ - 1.2, 12, 1.2, 1.2, [0.32, 0.35, 0.40]);

              // 타워 외벽 코발트 블루 수직 파이론 액센트 라인
              mesh.addBox(cell.x + 8.5, cell.y + 0.6, pilotiH, 2.5, 0.8, height - pilotiH, [0.12, 0.38, 0.78]);
              mesh.addBox(cell.x + 33.0, cell.y + 0.6, pilotiH, 2.5, 0.8, height - pilotiH, [0.12, 0.38, 0.78]);

              // 옥탑 프레임 윙
              mesh.addBox(cell.x + 3.5, cell.y + 3.5, height, 12, 15, 4.2, [0.65, 0.68, 0.74]);
              mesh.addBox(cell.x + 28.5, cell.y + 3.5, height, 12, 15, 4.2, [0.65, 0.68, 0.74]);

              // 단지 내 야외 광장 (우레탄 배드민턴 코트 + 휴게 파고라 + 조경수)
              // 배드민턴 코트 (10m x 6m)
              mesh.addBox(cell.x + 18, cell.y + aptD - 5.5, 0.08, 9, 5, 0.06, [0.20, 0.55, 0.42]); // 녹색 코트
              mesh.addBox(cell.x + 22.3, cell.y + aptD - 5.5, 0.14, 0.4, 5, 0.85, [0.95, 0.95, 0.98]); // 네트
              // 목재 덩굴 파고라 휴게 쉼터
              mesh.addPillar(cell.x + 19, cell.y + 19, 0.1, 3.2, 0.2, [0.45, 0.35, 0.25]);
              mesh.addPillar(cell.x + 25, cell.y + 19, 0.1, 3.2, 0.2, [0.45, 0.35, 0.25]);
              mesh.addBox(cell.x + 18, cell.y + 18, 3.2, 8, 3.0, 0.25, [0.55, 0.42, 0.30]);
              mesh.addTree(cell.x + 22, cell.y + 19.5, 0.1, 9, 3.5, 'pine');
            }
          }
        }

        // 2) 중심상업지구 글래스 타워 & 쇼핑몰 (3대 특화 모델: 셋백 타워, 원형 로툰다, 트윈 복합몰)
        else if (cell.type === 'commercial') {
          if (cell.x % 48 === 0 && cell.y % 48 === 0) {
            const modelType = Math.abs(Math.floor(cell.x / 48) + Math.floor(cell.y / 48)) % 3;
            let comW = 40, comD = 38;
            if (modelType === 1) { comW = 36; comD = 36; }
            else if (modelType === 2) { comW = 42; comD = 36; }

            if (fp.isOverlapping(cell.x, cell.y, cell.x + comW, cell.y + comD, 6.0)) {
              continue;
            }
            fp.addBox(cell.x, cell.y, cell.x + comW, cell.y + comD, 'building_commercial', { modelType });

            // [Commercial Model 0] 계단식 셋백 커튼월 타워 & 쇼핑몰 스트리트 (화려한 네온 간판, 옥상 카페 테라스, 첨탑 & 팝젯 분수광장)
            if (modelType === 0) {
              const comHeight = 85 + ((cell.x * 19 + cell.y * 31) % 45); // 85m ~ 130m
              const podiumH = 14.0;

              // 1~3층 스트리트몰 상가 포디엄
              mesh.addBox(cell.x, cell.y, 0, comW, comD, podiumH, [0.40, 0.44, 0.48], [0.30, 0.60, 0.35]);
              // 1층 쇼핑몰 아케이드 전광판 & 글래스 쇼윈도
              mesh.addBox(cell.x + 2, cell.y - 0.5, 0.5, comW - 4, 1.2, 4.5, [0.88, 0.92, 0.98, 1.4]);
              // 화려한 상업 네온 사인 밴드 (오렌지 / 시안)
              mesh.addBox(cell.x + 3, cell.y - 0.7, 5.2, comW * 0.45, 0.8, 1.8, [0.98, 0.45, 0.15, 1.8]);
              mesh.addBox(cell.x + comW * 0.5, cell.y - 0.7, 5.2, comW * 0.45, 0.8, 1.8, [0.12, 0.85, 0.78, 1.8]);

              // 포디엄 옥상 루프가든 테라스 (목재 데크, 야외 카페 파라솔, 식재 플랜터)
              mesh.addBox(cell.x + 2, cell.y + 2, podiumH, comW - 4, comD - 4, 0.3, [0.24, 0.64, 0.32]);
              mesh.addBox(cell.x + 4, cell.y + 4, podiumH + 0.3, 10, 6, 0.25, [0.65, 0.52, 0.40]); // 목재 데크
              // 야외 파라솔 2조
              mesh.addPillar(cell.x + 7, cell.y + 7, podiumH + 0.5, podiumH + 3.2, 0.08, [0.90, 0.92, 0.95]);
              mesh.addBox(cell.x + 5.2, cell.y + 5.2, podiumH + 3.2, 3.6, 3.6, 0.3, [0.95, 0.92, 0.88]);

              // 2단 셋백 고층 글래스 커튼월 타워
              mesh.addBox(cell.x + 3.5, cell.y + 3.5, podiumH, comW - 7.0, comD - 7.0, comHeight * 0.65 - podiumH, [0.18, 0.56, 0.88, 1.45]);
              mesh.addBox(cell.x + 6.0, cell.y + 6.0, comHeight * 0.65, comW - 12.0, comD - 12.0, comHeight * 0.35, [0.15, 0.60, 0.92, 1.48]);

              // 옥상 45도 사선 경사 크라운 루프 & 첨탑 안테나 마스트 & BMU 곤돌라 레일
              mesh.addBox(cell.x + 8.0, cell.y + 8.0, comHeight, comW - 16.0, comD - 16.0, 5.5, [0.85, 0.90, 0.96, 1.4]);
              mesh.addPillar(cell.x + comW * 0.5, cell.y + comD * 0.5, comHeight + 5.5, comHeight + 18.0, 0.38, [0.95, 0.96, 0.98]);

              // 전면 광장 팝젯 분수 및 모던 스테인리스 조형물
              mesh.addBox(cell.x + 6, cell.y - 3.5, 0.05, comW - 12, 3.5, 0.15, [0.75, 0.78, 0.82]);
              mesh.addBox(cell.x + 10, cell.y - 2.5, 0.20, 2.0, 2.0, 0.15, [0.20, 0.65, 0.95, 1.5]); // 팝젯 분수
              mesh.addPillar(cell.x + comW - 10, cell.y - 2.0, 0.2, 4.5, 0.35, [0.95, 0.78, 0.22, 1.4]); // 현대 조형물
            }

            // [Commercial Model 1] 원형/다각 라운드 글래스 로툰다 타워 (16각 커튼월 루버핀, 캔틸레버 공중정원, 돔 스카이라운지)
            else if (modelType === 1) {
              const comHeight = 75 + ((cell.x + cell.y) % 40); // 75m ~ 115m
              const radius = comW * 0.48;
              const cx = cell.x + comW * 0.5;
              const cy = cell.y + comD * 0.5;

              // 원형 실린더 프리즘 타워 본체
              mesh.addCylinder(cx, cy, 0, comHeight, radius, [0.20, 0.58, 0.86, 1.4], [0.22, 0.65, 0.38], 16);

              // 16방향 수직 알루미늄 일사차폐 루버 핀 (Spandrel Fins)
              for (let a = 0; a < 16; a++) {
                const ang = (a / 16) * Math.PI * 2;
                const fx = cx + Math.cos(ang) * (radius + 0.4);
                const fy = cy + Math.sin(ang) * (radius + 0.4);
                mesh.addPillar(fx, fy, 4.0, comHeight - 4.0, 0.22, [0.92, 0.94, 0.98]);
              }

              // 중간층 캔틸레버 공중정원 (Sky Garden)
              const skyGardenZ = comHeight * 0.52;
              mesh.addCylinder(cx, cy, skyGardenZ - 3.5, skyGardenZ + 3.5, radius + 0.8, [0.85, 0.92, 0.98, 1.5], null, 16);
              mesh.addTree(cx + 4, cy, skyGardenZ + 3.5, 6.5, 2.5, 'cherry');

              // 옥상 스카이 레스토랑 & 돔 루프 비콘
              mesh.addCylinder(cx, cy, comHeight, comHeight + 6.0, radius * 0.75, [0.92, 0.94, 0.98], [0.15, 0.55, 0.88], 16);
              mesh.addPillar(cx, cy, comHeight + 6.0, comHeight + 11.0, 0.3, [0.98, 0.85, 0.20, 2.0]);

              // 전면 원형 화강석 포장 광장 & 조경 벤치
              mesh.addCurbRing(cx, cell.y - 1.5, 0.05, 0.3, radius * 0.6, 1.2, [0.82, 0.85, 0.88], [0.25, 0.60, 0.30]);
            }

            // [Commercial Model 2] 복합 트윈 오피스 & 글래스 아트리움 몰 (초대형 곡면 볼트 지붕, 사선 스카이워크 & 썬큰 진입부)
            else {
              const comHeight = 78 + ((cell.x * 13 + cell.y * 7) % 42); // 78m ~ 120m
              const podiumH = 15.0;

              // 저층 1~4층 쇼핑몰 기단부 & 초대형 곡면 글래스 볼트 아트리움
              mesh.addBox(cell.x, cell.y, 0, comW, comD, podiumH, [0.38, 0.42, 0.48], [0.88, 0.92, 0.98, 1.4]);
              // 중앙 글래스 채광 볼트 지붕 (Barrel Vault)
              mesh.addCurvedVault(cell.x + 12, cell.y + 4, podiumH, 18, comD - 8, 4.5, [0.35, 0.72, 0.95, 1.45]);

              // 2개의 트윈 오피스 타워 (서측 타워 & 동측 타워)
              mesh.addBox(cell.x + 2, cell.y + 3, podiumH, 17, comD - 6, comHeight - podiumH, [0.18, 0.55, 0.85, 1.4]);
              mesh.addBox(cell.x + 23, cell.y + 3, podiumH, 17, comD - 6, comHeight - podiumH, [0.18, 0.55, 0.85, 1.4]);

              // 상부 스카이워크 연결 브릿지 (공중 회랑)
              mesh.addBox(cell.x + 17, cell.y + 10, comHeight * 0.65, 8, 16, 6.0, [0.88, 0.92, 0.98, 1.45]);

              // 전면 미디어 파사드 대형 LED 스크린
              mesh.addBox(cell.x + 6, cell.y - 0.4, 4.0, comW - 12, 0.6, 7.5, [0.12, 0.70, 0.95, 1.7]);

              // 전면 썬큰 광장 (화강석 계단 스탠드 및 플랜터)
              mesh.addBox(cell.x + 6, cell.y - 2.5, 0.05, comW - 12, 3.2, 0.35, [0.75, 0.78, 0.82]);
              mesh.addBox(cell.x + 7, cell.y - 2.0, 0.40, 4.0, 2.0, 0.5, [0.24, 0.62, 0.30]);
            }
          }
        }

        // 3) 판교형 테크노밸리 R&D 캠퍼스 (3대 특화 모델: 중정형 본관, L자형 테크랩, 트윈 랩)
        else if (cell.type === 'industrial') {
          if (cell.x % 64 === 0 && cell.y % 48 === 0) {
            const modelType = Math.abs(Math.floor(cell.x / 64) + Math.floor(cell.y / 48)) % 3;
            let rdW = 54, rdD = 36;
            if (modelType === 1) { rdW = 50; rdD = 36; }
            else if (modelType === 2) { rdW = 52; rdD = 36; }

            if (fp.isOverlapping(cell.x, cell.y, cell.x + rdW, cell.y + rdD, 6.0)) {
              continue;
            }
            fp.addBox(cell.x, cell.y, cell.x + rdW, cell.y + rdD, 'building_industrial', { modelType });

            // [Industrial Model 0] 친환경 중정형 R&D 헤드쿼터 (샴페인 골드 루버, 중앙 보이드 수경정원, 태양광 PV 매트릭스 & EV 충전소)
            if (modelType === 0) {
              const rdHeight = 34 + ((cell.x + cell.y) % 16); // 34m ~ 50m
              // 메인 사각 링 매스 (외곽 샴페인 메탈릭 & 글래스)
              mesh.addBox(cell.x + 1.5, cell.y + 1.5, 0, rdW - 3.0, rdD - 3.0, rdHeight, [0.30, 0.62, 0.88, 1.35], [0.85, 0.88, 0.92]);
              // 중앙 야외 중정(Atrium) 보이드 (18m x 14m)
              mesh.addBox(cell.x + 18, cell.y + 11, 0.05, 18, 14, 0.2, [0.26, 0.64, 0.32]); // 잔디 바닥
              mesh.addBox(cell.x + 20, cell.y + 13, 0.20, 14, 10, 0.15, [0.15, 0.52, 0.82, 1.35]); // 수경 반사 연못
              mesh.addBox(cell.x + 24, cell.y + 11, 0.25, 6, 14, 0.12, [0.65, 0.52, 0.40]); // 목재 산책 보드워크
              mesh.addTree(cell.x + 27, cell.y + 18, 0.3, 11, 4.2, 'pine'); // 상징목 소나무

              // 수평 알루미늄 차양 루버 핀 (Brise-soleil)
              for (let lz = 6; lz < rdHeight; lz += 6.8) {
                mesh.addBox(cell.x + 1.0, cell.y + 1.0, lz, rdW - 2.0, rdD - 2.0, 0.65, [0.85, 0.82, 0.74]);
              }

              // 옥상 고밀도 그린에너지 태양광 PV 매트릭스 2열 & 공조 펜트하우스
              mesh.addBox(cell.x + 4, cell.y + 3, rdHeight, rdW * 0.22, rdD - 6, 0.6, [0.12, 0.20, 0.38]);
              mesh.addBox(cell.x + rdW - 16, cell.y + 3, rdHeight, rdW * 0.22, rdD - 6, 0.6, [0.12, 0.20, 0.38]);
              mesh.addBox(cell.x + 18, cell.y + 3, rdHeight, 18, 5, 2.8, [0.55, 0.58, 0.62]); // HVAC 실외기 루버실

              // 전면 EV 전기차 충전 스테이션 및 스마트 캐노피
              mesh.addBox(cell.x + 4, cell.y - 2.5, 0.1, 14, 3.0, 0.15, [0.22, 0.24, 0.26]);
              mesh.addBox(cell.x + 5, cell.y - 2.0, 0.25, 12, 2.2, 2.6, [0.85, 0.88, 0.92]);
              mesh.addBox(cell.x + 7, cell.y - 1.5, 0.25, 1.2, 0.8, 1.4, [0.15, 0.65, 0.92, 1.5]); // 충전기
              mesh.addBox(cell.x + 12, cell.y - 1.5, 0.25, 1.2, 0.8, 1.4, [0.15, 0.65, 0.92, 1.5]);
            }

            // [Industrial Model 1] L자형 스마트 테크 랩 & 테크 플라자 (캔틸레버 플로팅 매스, 키네틱 조형물 & 코워킹 파고라)
            else if (modelType === 1) {
              const rdHeight = 32 + ((cell.x * 7 + cell.y * 3) % 15); // 32m ~ 47m
              // L자형 매스: 주익(50m x 16m) + 측익(18m x 20m)
              mesh.addBox(cell.x + 1.5, cell.y + 1.5, 0, rdW - 3.0, 15, rdHeight, [0.28, 0.58, 0.85, 1.35]);
              mesh.addBox(cell.x + 1.5, cell.y + 16.5, 0, 17, rdD - 18, rdHeight, [0.28, 0.58, 0.85, 1.35]);

              // 캔틸레버 돌출 상층부 (2~4층 오버행)
              mesh.addBox(cell.x + 18, cell.y + 15, 4.5, 16, 8, rdHeight - 4.5, [0.22, 0.24, 0.28]);

              // 코너 오픈 테크 플라자 (목재 데크, 키네틱 조형물, 코워킹 파고라 & 공유자전거)
              mesh.addBox(cell.x + 20, cell.y + 18, 0.08, rdW - 22, rdD - 20, 0.22, [0.65, 0.52, 0.40]);
              mesh.addPillar(cell.x + 32, cell.y + 26, 0.3, 8.5, 0.45, [0.95, 0.78, 0.25, 1.4]); // 테크 조형물
              // 코워킹 파고라 테이블
              mesh.addBox(cell.x + 24, cell.y + 22, 0.3, 5.0, 3.2, 0.45, [0.35, 0.38, 0.42]);
              mesh.addBox(cell.x + 23, cell.y + 21, 3.2, 7.0, 5.0, 0.25, [0.45, 0.35, 0.25]); // 지붕
              // 공유 스마트 모빌리티 랙
              mesh.addBox(cell.x + rdW - 10, cell.y + 19, 0.3, 6.0, 1.8, 0.75, [0.22, 0.65, 0.35]);
            }

            // [Industrial Model 2] 트윈 랩 & 공중 글래스 스카이워크 (클린룸 HVAC 대형 설비, 위성 안테나 & 바이오스웨일 정원)
            else {
              const rdHeight = 28 + ((cell.x + cell.y) % 15); // 28m ~ 43m
              // 연구동 A (21m x 33m) & 연구동 B (21m x 33m), 중앙 9m 간격
              mesh.addBox(cell.x + 1.5, cell.y + 1.5, 0, 21, rdD - 3.0, rdHeight, [0.32, 0.62, 0.88, 1.35]);
              mesh.addBox(cell.x + 29.5, cell.y + 1.5, 0, 21, rdD - 3.0, rdHeight, [0.32, 0.62, 0.88, 1.35]);

              // 3~4층 높이 공중 글래스 스카이워크 브릿지
              mesh.addBox(cell.x + 21, cell.y + 10, 12, 10, 16, 6.0, [0.88, 0.92, 0.98, 1.45]);

              // 옥상 첨단 클린룸 HVAC 공조 설비, 냉각탑 실린더 및 위성 통신 디스크
              mesh.addBox(cell.x + 5, cell.y + 6, rdHeight, 14, rdD - 12, 3.5, [0.72, 0.75, 0.80]);
              mesh.addBox(cell.x + 33, cell.y + 6, rdHeight, 14, rdD - 12, 3.5, [0.72, 0.75, 0.80]);
              // 원통형 냉각탑 2기
              mesh.addCylinder(cell.x + 12, cell.y + rdD * 0.5, rdHeight + 3.5, rdHeight + 6.2, 2.2, [0.65, 0.68, 0.72], [0.55, 0.58, 0.62], 8);
              mesh.addCylinder(cell.x + 40, cell.y + rdD * 0.5, rdHeight + 3.5, rdHeight + 6.2, 2.2, [0.65, 0.68, 0.72], [0.55, 0.58, 0.62], 8);
              // 위성 통신 파라볼라 안테나 모형
              mesh.addPillar(cell.x + 8, cell.y + 10, rdHeight + 3.5, rdHeight + 6.5, 0.25, [0.92, 0.94, 0.98]);
              mesh.addBox(cell.x + 6.5, cell.y + 9.0, rdHeight + 6.5, 3.0, 2.0, 0.35, [0.96, 0.97, 0.99]);

              // 중앙 캠퍼스 바이오스웨일 레인가든 (Bioswale Rain Garden)
              mesh.addBox(cell.x + 22.5, cell.y + 4, 0.05, 7.0, rdD - 8, 0.15, [0.30, 0.62, 0.35]);
              mesh.addTree(cell.x + 26, cell.y + 10, 0.2, 8, 3.2, 'pine');
              mesh.addTree(cell.x + 26, cell.y + rdD - 10, 0.2, 8, 3.2, 'pine');
            }
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
    // 실시간 교차로 신호등 동적 렌더링 (node.signal & sim.simulationTime)
    // ===================================================================
    renderSignals(mesh) {
      const sim = this.sim;
      if (!sim || !sim.nodes) return;

      const simTime = sim.simulationTime || 0;
      // 발광(Lit) 및 소등(Dim) 램프 색상 정의
      const litRed = [1.0, 0.12, 0.12, 2.4];
      const dimRed = [0.22, 0.05, 0.05, 0.7];
      const litYellow = [1.0, 0.82, 0.15, 2.4];
      const dimYellow = [0.22, 0.18, 0.04, 0.7];
      const litGreen = [0.12, 0.98, 0.38, 2.4];
      const dimGreen = [0.04, 0.22, 0.10, 0.7];

      for (const node of sim.nodes) {
        if (!node.signal) continue;
        const signal = node.signal;
        const cycle = signal.cycle || 60;
        const nsGreenTime = signal.northSouthGreen || 35;
        const phase = simTime % cycle;

        // 3현시 신호 타이밍: Green -> Yellow (전환 직전 3.5초) -> Red
        const nsYellowDuration = 3.5;
        const ewYellowDuration = 3.5;

        const isNSGreen = phase < (nsGreenTime - nsYellowDuration);
        const isNSYellow = !isNSGreen && (phase < nsGreenTime);
        const isEWGreen = !isNSGreen && !isNSYellow && (phase < cycle - ewYellowDuration);
        const isEWYellow = !isNSGreen && !isNSYellow && !isEWGreen;

        const nsRedCol = (isNSGreen || isNSYellow) ? dimRed : litRed;
        const nsYelCol = isNSYellow ? litYellow : dimYellow;
        const nsGrnCol = isNSGreen ? litGreen : dimGreen;

        const ewRedCol = (isEWGreen || isEWYellow) ? dimRed : litRed;
        const ewYelCol = isEWYellow ? litYellow : dimYellow;
        const ewGrnCol = isEWGreen ? litGreen : dimGreen;

        const cx = node.x, cy = node.y;

        // 1) 남북 방향 신호등 램프 (남북 주행 차량 대상)
        // 북행 차량용(남측 기둥 암) 및 남행 차량용(북측 기둥 암)
        // [hx, hy, faceDir]
        const nsHousings = [
          [cx - 5.5, cy - 14.9, 1],  // 남측 신호등 (Y 증가 방향 주행 차량이 바라봄)
          [cx + 5.5, cy + 14.9, -1]  // 북측 신호등 (Y 감소 방향 주행 차량이 바라봄)
        ];
        for (const [hx, hy, faceDir] of nsHousings) {
          const lz = 7.35;
          const ly = hy - faceDir * 0.25;
          // 가로 3구 램프 (적 - 황 - 녹)
          mesh.addBox(hx - 0.46, ly, lz - 0.16, 0.28, 0.08, 0.32, nsRedCol);
          mesh.addBox(hx - 0.14, ly, lz - 0.16, 0.28, 0.08, 0.32, nsYelCol);
          mesh.addBox(hx + 0.18, ly, lz - 0.16, 0.28, 0.08, 0.32, nsGrnCol);
        }

        // 2) 동서 방향 신호등 램프 (동서 주행 차량 대상)
        // 동행 차량용(서측 기둥 암) 및 서행 차량용(동측 기둥 암)
        const ewHousings = [
          [cx - 14.9, cy - 5.5, 1],  // 서측 신호등 (X 증가 방향 주행 차량이 바라봄)
          [cx + 14.9, cy + 5.5, -1]  // 동측 신호등 (X 감소 방향 주행 차량이 바라봄)
        ];
        for (const [hx, hy, faceDir] of ewHousings) {
          const lz = 7.35;
          const lx = hx - faceDir * 0.25;
          // 가로 3구 램프 (적 - 황 - 녹)
          mesh.addBox(lx, hy - 0.46, lz - 0.16, 0.08, 0.28, 0.32, ewRedCol);
          mesh.addBox(lx, hy - 0.14, lz - 0.16, 0.08, 0.28, 0.32, ewYelCol);
          mesh.addBox(lx, hy + 0.18, lz - 0.16, 0.08, 0.28, 0.32, ewGrnCol);
        }

        // 3) 교차로 노면 정지선 신호 상태 표시 (신호 대기 시각성 극대화)
        const nsStopCol = (isNSGreen || isNSYellow) ? [0.95, 0.95, 0.98, 1.0] : [0.98, 0.18, 0.18, 1.8];
        const ewStopCol = (isEWGreen || isEWYellow) ? [0.95, 0.95, 0.98, 1.0] : [0.98, 0.18, 0.18, 1.8];

        // 남북 정지선 보조 발광
        mesh.addBox(cx - 12.0, cy - 17.5, 0.18, 8.6, 0.42, 0.02, nsStopCol);
        mesh.addBox(cx + 3.4, cy + 17.5, 0.18, 8.6, 0.42, 0.02, nsStopCol);

        // 동서 정지선 보조 발광
        mesh.addBox(cx - 17.5, cy - 12.0, 0.18, 0.42, 8.6, 0.02, ewStopCol);
        mesh.addBox(cx + 17.5, cy + 3.4, 0.18, 0.42, 8.6, 0.02, ewStopCol);
      }
    }

    // ===================================================================
    // 실시간 3D 차량 시뮬레이션 렌더링 (BRT 버스 vs 일반 승용차 차별화)
    // ===================================================================
    renderCars(targetMesh) {
      const sim = this.sim;
      if (!sim || !sim.cars || sim.cars.length === 0) return;

      const mesh = targetMesh || new MeshData();
      const nodeMap = new Map();
      for (const n of sim.nodes) nodeMap.set(n.id, n);

      // 일반 승용차용 세련된 한국 도심 컬러 팔레트
      const carPalette = [
        [0.94, 0.95, 0.97], // 펄 화이트
        [0.72, 0.75, 0.78], // 메탈릭 실버
        [0.30, 0.32, 0.36], // 다크 그레이
        [0.14, 0.15, 0.18], // 팬텀 블랙
        [0.18, 0.32, 0.55], // 미드나잇 블루
        [0.68, 0.20, 0.22]  // 버건디 레드
      ];

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

        const isBrt = car.kind === 'bus';
        const isStopped = (car.dwell && car.dwell > 0) || (car.speed === 0);
        const cosA = Math.cos(angle), sinA = Math.sin(angle);

        if (isBrt) {
          // ========================================================
          // [대형 BRT 광역급행 버스] 한국 M-Bus / 세종 BRT 규격 (12.6m)
          // ========================================================
          const bLen = 12.6, bWid = 2.8, bH = 3.4;

          // 1) 하부 차체 섀시 (다크 차콜 휠하우스/범퍼)
          mesh.addOrientedBox(curX, curY, curZ + 0.35, bLen, bWid, 0.7, angle, [0.20, 0.22, 0.25], [0.25, 0.27, 0.30]);

          // 2) 메인 바디 (한국 광역급행 M-Bus 시그니처 레드 투톤)
          const redBody = [0.88, 0.16, 0.18];
          mesh.addOrientedBox(curX, curY, curZ + 1.25, bLen, bWid, 1.2, angle, redBody, redBody);

          // 3) 파노라믹 틴팅 글래스 창문 라인
          mesh.addOrientedBox(curX, curY, curZ + 2.15, bLen * 0.94, bWid + 0.05, 0.85, angle, [0.12, 0.16, 0.22], [0.12, 0.16, 0.22]);

          // 4) 화이트/실버 에어로 루프 상판
          mesh.addOrientedBox(curX, curY, curZ + 2.85, bLen, bWid, 0.65, angle, [0.92, 0.94, 0.96], [0.94, 0.96, 0.98]);

          // 5) 루프 에어컨 공조기 유닛 2기
          const acOffset = bLen * 0.28;
          for (const s of [-1, 1]) {
            const acX = curX + cosA * (acOffset * s);
            const acY = curY + sinA * (acOffset * s);
            mesh.addOrientedBox(acX, acY, curZ + 3.35, 2.2, 1.5, 0.42, angle, [0.88, 0.90, 0.94], [0.94, 0.96, 0.98]);
          }

          // 6) 전면 상단 디지털 LED 전광판 (오렌지/호박색 행선판)
          const fHead = bLen * 0.49;
          const fX = curX + cosA * fHead;
          const fY = curY + sinA * fHead;
          mesh.addOrientedBox(fX, fY, curZ + 2.55, 0.35, bWid * 0.65, 0.4, angle, [1.0, 0.78, 0.18, 1.8]);

          // 7) 전면 듀얼 LED 헤드라이트 (앞범퍼 좌우)
          const hlDist = bLen * 0.495;
          const hlW = bWid * 0.35;
          const hlX = curX + cosA * hlDist;
          const hlY = curY + sinA * hlDist;
          const perpX = -sinA * hlW, perpY = cosA * hlW;
          mesh.addOrientedBox(hlX + perpX, hlY + perpY, curZ + 0.55, 0.3, 0.55, 0.35, angle, [1.0, 1.0, 0.92, 1.8]);
          mesh.addOrientedBox(hlX - perpX, hlY - perpY, curZ + 0.55, 0.3, 0.55, 0.35, angle, [1.0, 1.0, 0.92, 1.8]);

          // 8) 후면 테일램프/브레이크등 (정차 시 비상등/브레이크등 발광 강화)
          const tlDist = -bLen * 0.495;
          const tlX = curX + cosA * tlDist;
          const tlY = curY + sinA * tlDist;
          const tlColor = isStopped ? [1.0, 0.05, 0.05, 2.4] : [0.95, 0.12, 0.12, 1.6];
          mesh.addOrientedBox(tlX + perpX, tlY + perpY, curZ + 0.65, 0.25, 0.5, 0.5, angle, tlColor);
          mesh.addOrientedBox(tlX - perpX, tlY - perpY, curZ + 0.65, 0.25, 0.5, 0.5, angle, tlColor);
        } else {
          // ========================================================
          // [일반 도심 승용차] 세단 / SUV (길이 4.6m, 폭 2.05m)
          // ========================================================
          const cLen = 4.6, cWid = 2.05, cH = 1.55;

          // 차체 색상 (차량 ID 기반으로 균형 잡힌 도심 세단 컬러 매핑)
          let bodyColor;
          if (car.color && car.color !== '#e74c3c') {
            bodyColor = [0.85, 0.85, 0.90];
          } else {
            const seed = Math.abs(Math.sin((car.id || 1) * 9973));
            bodyColor = carPalette[Math.floor(seed * carPalette.length) % carPalette.length];
          }

          // 1) 하부 차체 섀시 (차체 컬러)
          mesh.addOrientedBox(curX, curY, curZ + 0.38, cLen, cWid, 0.75, angle, bodyColor, bodyColor);

          // 2) 상부 캐빈 (틴팅 윈드실드/유리창 & 루프)
          const cabinLen = cLen * 0.55;
          const cabOffset = -cLen * 0.06;
          const cabX = curX + cosA * cabOffset;
          const cabY = curY + sinA * cabOffset;
          mesh.addOrientedBox(cabX, cabY, curZ + 1.05, cabinLen, cWid * 0.88, 0.68, angle, [0.14, 0.17, 0.22], bodyColor);

          // 3) 전면 헤드라이트 (좌우 2개)
          const hlDist = cLen * 0.485;
          const hlW = cWid * 0.34;
          const hlX = curX + cosA * hlDist;
          const hlY = curY + sinA * hlDist;
          const perpX = -sinA * hlW, perpY = cosA * hlW;
          mesh.addOrientedBox(hlX + perpX, hlY + perpY, curZ + 0.35, 0.25, 0.38, 0.25, angle, [1.0, 1.0, 0.88, 1.6]);
          mesh.addOrientedBox(hlX - perpX, hlY - perpY, curZ + 0.35, 0.25, 0.38, 0.25, angle, [1.0, 1.0, 0.88, 1.6]);

          // 4) 후면 테일라이트 (좌우 2개)
          const tlDist = -cLen * 0.485;
          const tlX = curX + cosA * tlDist;
          const tlY = curY + sinA * tlDist;
          mesh.addOrientedBox(tlX + perpX, tlY + perpY, curZ + 0.38, 0.22, 0.35, 0.22, angle, [0.95, 0.15, 0.15, 1.5]);
          mesh.addOrientedBox(tlX - perpX, tlY - perpY, curZ + 0.38, 0.22, 0.35, 0.22, angle, [0.95, 0.15, 0.15, 1.5]);
        }
      }

      // targetMesh가 주어지지 않은 단독 호출일 경우 버퍼 바인딩 및 드로우
      if (!targetMesh) {
        this.flushDynamicMesh(mesh);
      }
    }

    // ===================================================================
    // 동적 레이어 일괄 드로우 (신호등 램프 + 차량 시뮬레이션 통합)
    // ===================================================================
    renderDynamicLayer() {
      const mesh = new MeshData();
      this.renderSignals(mesh);
      this.renderCars(mesh);
      this.flushDynamicMesh(mesh);
    }

    flushDynamicMesh(mesh) {
      if (!mesh || mesh.indices.length === 0) return;
      const gl = this.gl;

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

      this.renderDynamicLayer();
    }
  }

  CityView3D.FootprintManager = FootprintManager;
  global.CityView3D = CityView3D;
  global.FootprintManager = FootprintManager;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CityView3D, FootprintManager, Mat4, MeshData };
  }
})(typeof window !== 'undefined' ? window : this);
