# 신탄진·금강·대전 광역권 Cities: Skylines 2 / 1 하이트맵 & 자원맵 가이드

본 패키지는 사용자의 요청에 따라 **금강 본류 및 경부고속도로 금강교·신탄진을 최북단(맨 위)으로 기준** 삼아, **시티즈 2(14.336km × 14.336km) 및 시티즈 1(17.28km) 맵이 담을 수 있는 최대 범위**의 실제 수치표고모델(DEM) 16비트 하이트맵과 자원맵(Resource Map)을 구축한 공식 규격 데이터셋입니다.

---

## 1. 지리적 경계 및 규격 (Geographic Bounds)

* **북단 (맨 위 / Top Border)**: 위도 `36.4585° N` (금강 본류, 경부고속도로 금강교, 경부고속선 KTX 철교)
* **남단 (맨 아래 / Bottom Border)**: 위도 `36.3295° N` (대전정부청사, 둔산 신도시, 탄방동, 갑천 중류)
* **서단 (좌측 / West Border)**: 경도 `127.3321° E` (유성온천, KAIST, 충남대학교, 대덕연구개발특구 서측)
* **동단 (우측 / East Border)**: 경도 `127.4919° E` (계족산 423m 주능선, 계족산성, 대청호 수변)
* **맵 실측 면적**: **14,336 m × 14,336 m** (가로 14.34 km × 세로 14.34 km, 총 면적 205.5 ㎢)
* **해발고도 범위**: 최저 `13.5m` (금강 하상 바닥 준설) ~ 최고 `424.5m` (계족산 주봉)

---

## 2. 생성된 파일 목록

| 파일명 | 해상도 / 포맷 | 설명 |
| :--- | :--- | :--- |
| **`heightmap_cs2_4096_std.png`** | 4096×4096 / 16-bit PNG | **[추천] 시티즈 2 공식 물리 규격 하이트맵** (1m당 16레벨 실측 매핑) |
| **`heightmap_cs2_4096_normalized.png`** | 4096×4096 / 16-bit PNG | **시티즈 2 전역 최대 정밀도 정규화 하이트맵** (0~65535 풀 다이내믹 레인지) |
| **`heightmap_cs1_1081.png`** | 1081×1081 / 16-bit PNG | **시티즈 1(Cities: Skylines 1) 표준 하이트맵** |
| **`resource_fertile_4096.png`** | 4096×4096 / 8-bit PNG | **비옥한 토지(Fertile Land)**: 갑천·금강 충적 평야 농경지 |
| **`resource_forest_4096.png`** | 4096×4096 / 8-bit PNG | **산림 자원(Forest/Wood)**: 계족산맥 및 도심 산림 녹지축 |
| **`resource_ore_4096.png`** | 4096×4096 / 8-bit PNG | **광물 자원(Ore/Minerals)**: 계족산 급경사 화강암반 및 채석장 |
| **`resource_oil_4096.png`** | 4096×4096 / 8-bit PNG | **석유/화학공업(Oil)**: 한국타이어 대전공장 및 SK/현대 대형 유류저장단지 |
| **`resource_underground_water_4096.png`** | 4096×4096 / 8-bit PNG | **지하수 수자원(Underground Water)**: 하천변 대수층 |
| **`preview_topography_hillshade.png`** | 2048×2048 / RGB | 고정밀 음영기복도(Hillshade) 및 등고 채색 미리보기 |
| **`preview_resources_combined.png`** | 2048×2048 / RGB | 5대 자원 종합 분포 시각화 맵 (한글 범례 포함) |
| **`preview_map_regions_annotated.png`** | 2048×2048 / RGB | 주요 랜드마크·교통축 핀포인트 표시 위성 지도 |

---

## 3. Cities: Skylines 2 맵 에디터 적용 가이드

1. **하이트맵 경로 복사**:
   - `heightmap_cs2_4096_std.png` (또는 `heightmap_cs2_4096_normalized.png`) 파일을 아래 CS2 사용자 맵 폴더에 복사합니다:
     `%UserProfile%\AppData\LocalLow\Colossal Order\Cities Skylines II\Maps\` (또는 `Heightmaps\`)
2. **맵 에디터(Map Editor) 실행**:
   - CS2 실행 후 `지도 에디터 (Map Editor)` 진입 -> `지형(Terrain)` 탭 선택.
   - `높이맵 가져오기 (Import Heightmap)` 클릭 후 복사한 파일 선택.
   - **권장 설정값**:
     - **최대 고도 (Max Height)**: `500.0 m`
     - **해수면 기준 높이 (Sea Level)**: `24.0 m`
3. **자원 맵(Resource Map) 가져오기**:
   - 지형 툴의 `자원 (Resources)` 탭 -> 각 자원(비옥한 땅, 숲, 광물, 기름, 지하수)별 `가져오기 (Import)` 클릭.
   - 매칭되는 `resource_*_4096.png` 파일을 지정하면 실제 대전/신탄진 지형에 맞게 정확히 자원이 배치됩니다.
4. **수계(Water) 시뮬레이션 활성화**:
   - 북단 금강 본류와 남측 갑천 상류에 `수원지(Water Source)`를 배치하고 유량을 설정하면 자연스러운 하천 흐름이 형성됩니다.
