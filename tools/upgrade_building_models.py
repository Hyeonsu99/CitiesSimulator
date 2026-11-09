import os

VIEW3D_PATH = os.path.join(os.path.dirname(__file__), '..', 'view3d.js')

with open(VIEW3D_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

# Locate the zoneCells loop
start_marker = "      // 5-2. 주거 슈퍼블록, 중심상업, 테크노밸리 건축 에셋 고화질 배치 (발자국 AABB 검증 기반)"
end_marker = "    uploadStaticMesh(mesh) {"

idx_start = text.find(start_marker)
idx_end = text.find(end_marker)

assert idx_start != -1, "start_marker not found!"
assert idx_end != -1, "end_marker not found!"

new_building_code = '''      // 5-2. 주거 슈퍼블록, 중심상업, 테크노밸리 건축 에셋 초고화질 배치 (현실적 비례·재질·창문·야외공간 & AABB 충돌 방지 보장)
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
'''

new_text = text[:idx_start] + new_building_code + '\n' + text[idx_end:]

with open(VIEW3D_PATH, 'w', encoding='utf-8') as f:
    f.write(new_text)

print("[OK] All 10 architectural models upgraded with exceptional fidelity and outdoor amenities!")
