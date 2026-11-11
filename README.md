# Cities Skylines Toolkit

Cities: Skylines용 도시 설계, 건물 에셋 제작과 지형 맵 도구를 모은 저장소입니다. 도구는 각각 독립적으로 사용할 수 있으며, 주로 Cities: Skylines II를 대상으로 합니다.

## 빠른 시작

Windows에서 교통 시뮬레이터를 사용하려면 Python 3을 설치하고 `planner/run.bat`을 실행하세요. Edge가 설치되어 있으면 앱 창으로, 그렇지 않으면 기본 브라우저로 열립니다.

에셋 뷰어는 Node.js를 설치한 뒤 `asset-viewer` 폴더에서 `npm install`을 한 번 실행하고 `run.bat`을 실행하세요. 표시되는 로컬 주소에서 에셋을 확인할 수 있습니다.

## 구성

| 폴더 | 내용 | 필요 환경 및 안내 |
|---|---|---|
| [`planner/`](planner/) | 한국형 신도시 도로망·교통 시뮬레이터 | Python 3, 검증에는 Node.js · [사용법](planner/README.md) |
| [`cs2-kit/`](cs2-kit/) | CS2 건물 에셋 제작 키트와 프로젝트 | Python 3.9+, NumPy, Pillow; FBX와 LOD 검사에는 Blender 또는 bpy · [사용법](cs2-kit/README.md) |
| [`asset-viewer/`](asset-viewer/) | FBX/GLB 에셋 미리보기 | Node.js · [설정 안내](SETUP_AFTER_PULL.txt) |
| [`maps/`](maps/) | 신탄진 높이맵·자원맵과 생성 도구 | 결과물은 바로 사용 가능; 재생성에는 Python, NumPy, Pillow · [맵 가이드](maps/sintanjin/MAP_GUIDE.md) |
| [`skills/`](skills/) | Codex용 cs2-kit 스킬 | [스킬 안내](skills/cs2-kit/SKILL.md) |

다른 PC에서 설치하거나 각 도구의 환경을 설정할 때는 [설정 안내](SETUP_AFTER_PULL.txt)를 참고하세요.

## 사용 시 참고

- 플래너는 배치 정보를 JSON으로 내보냅니다. 게임에 적용하려면 해당 형식을 읽는 별도의 연동 수단이 필요합니다.
- 뷰어의 조명은 게임 화면을 근사한 것으로, 에셋의 최종 모양과 야간 표시 등은 게임에서 확인해야 합니다.
- `cs2-kit`의 라이선스는 [cs2-kit/LICENSE](cs2-kit/LICENSE)를 참고하세요. 저장소 전체에 적용되는 별도 라이선스는 아직 명시되지 않았습니다.
