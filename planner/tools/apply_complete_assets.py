import os

# Complete script to apply high-fidelity Korean New Town 3D assets to view3d.js
VIEW3D_PATH = os.path.join(os.path.dirname(__file__), '..', 'view3d.js')

with open(VIEW3D_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

# =========================================================================
# 1. buildRiverAndParks upgrade
# =========================================================================
old_river = """    // 2. 생태 하천과 수변공원 렌더러
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

      // 수변 만개한 벚나무, 소나무, 수양버들, 은행나무의 풍성한 식생
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

      // 수변 잔디 원형 야외공연장 (Circular Sunken Lawn)
      mesh.addCurbRing(1950, 920, 0.05, 0.35, 32, 3.5, [0.82, 0.85, 0.88], [0.24, 0.62, 0.32]);
    }"""

new_river = """    // 2. 생태 하천과 수변공원 렌더러 (다단 자연석 호안, 마리나 폰툰, 수변카페 파빌리온, 키네틱 조형물)
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
    }"""

assert old_river in text, "old_river not found!"
text = text.replace(old_river, new_river)

# =========================================================================
# 2. buildRoadNetworkAndInterchange upgrade (Sound barriers & Gantry sign)
# =========================================================================
old_road_rail = """            // 외곽 콘크리트 가드레일 방호벽 난간
            const railH = 1.1;
            mesh.addQuad(p1, p2, [p2[0], p2[1], curS.pz + 0.12 + railH], [p1[0], p1[1], prevS.pz + 0.12 + railH], [avgUx, avgUy, 0], [0.72, 0.75, 0.78]);
            mesh.addQuad([p4[0], p4[1], prevS.pz + 0.12 + railH], [p3[0], p3[1], curS.pz + 0.12 + railH], p3, p4, [-avgUx, -avgUy, 0], [0.72, 0.75, 0.78]);
          }

          prevS = curS;
        }"""

new_road_rail = """            // 외곽 콘크리트 가드레일 방호벽 난간
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
        }"""

assert old_road_rail in text, "old_road_rail not found!"
text = text.replace(old_road_rail, new_road_rail)

# =========================================================================
# 3. buildBenchmarkCentralCorridor upgrade (Tactile paving, bikes, beacons)
# =========================================================================
old_canopy_end = """        // 6) 정류장 진입 보행 슬로프 램프 (양방향 완만한 경사)
        mesh.addQuad([cx - pWid * 0.5, sy - pLen * 0.5 - 4.5, 0.15], [cx + pWid * 0.5, sy - pLen * 0.5 - 4.5, 0.15], [cx + pWid * 0.5, sy - pLen * 0.5, 0.15 + pH], [cx - pWid * 0.5, sy - pLen * 0.5, 0.15 + pH], [0, -1, 1], [0.72, 0.74, 0.78]);
        mesh.addQuad([cx - pWid * 0.5, sy + pLen * 0.5, 0.15 + pH], [cx + pWid * 0.5, sy + pLen * 0.5, 0.15 + pH], [cx + pWid * 0.5, sy + pLen * 0.5 + 4.5, 0.15], [cx - pWid * 0.5, sy + pLen * 0.5 + 4.5, 0.15], [0, 1, 1], [0.72, 0.74, 0.78]);
      }"""

new_canopy_end = """        // 6) 정류장 진입 보행 슬로프 램프 (양방향 완만한 경사)
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
      }"""

assert old_canopy_end in text, "old_canopy_end not found!"
text = text.replace(old_canopy_end, new_canopy_end)

# Also add tactile paving and yellow beacons to intersections
old_signal_pole = """        // 동북 모퉁이 (cx + 14.5, cy + 14.5)
        mesh.addPillar(cx + 14.5, cy + 14.5, 0.15, 7.8, 0.24, [0.22, 0.24, 0.28]);
        mesh.addBox(cx + 5.5, cy + 14.35, 7.5, 9.0, 0.32, 0.32, [0.22, 0.24, 0.28]);  // 남북용 암
        mesh.addBox(cx + 4.8, cy + 14.45, 7.05, 1.4, 0.45, 0.6, [0.12, 0.12, 0.14]);  // 남북용 하우징
        mesh.addBox(cx + 14.35, cy + 5.5, 7.5, 0.32, 9.0, 0.32, [0.22, 0.24, 0.28]);  // 동서용 암
        mesh.addBox(cx + 14.45, cy + 4.8, 7.05, 0.45, 1.4, 0.6, [0.12, 0.12, 0.14]);  // 동서용 하우징
      }"""

new_signal_pole = """        // 동북 모퉁이 (cx + 14.5, cy + 14.5)
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
      }"""

assert old_signal_pole in text, "old_signal_pole not found!"
text = text.replace(old_signal_pole, new_signal_pole)

with open(VIEW3D_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

print("[OK] River & Road & Infrastructure upgraded successfully!")
