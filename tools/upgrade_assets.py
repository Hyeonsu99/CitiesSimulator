import os

# Script to upgrade 3D assets in view3d.js
VIEW3D_PATH = os.path.join(os.path.dirname(__file__), '..', 'view3d.js')

with open(VIEW3D_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update addTree and add geometry helper methods in MeshData
old_add_tree = """    // 다양한 수종의 3D 나무 생성 (소나무, 벚나무, 수양버들, 은행나무, 느티나무)
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
      } else if (treeType === 'willow') {
        // 수변 수양버들 (연녹색 늘어진 버들 수관)
        this.addPillar(x, y, z, z + height * 0.55, 0.85, [0.40, 0.30, 0.22]);
        this.addBox(x - radius * 0.8, y - radius * 0.8, z + height * 0.4, radius * 1.6, radius * 1.6, height * 0.42, [0.35, 0.68, 0.28]);
        this.addBox(x - radius * 1.15, y - radius * 1.15, z + height * 0.22, radius * 2.3, radius * 2.3, height * 0.28, [0.28, 0.62, 0.24]);
      } else if (treeType === 'ginkgo') {
        // 황금빛 가을 은행나무
        this.addPillar(x, y, z, z + height * 0.45, 0.75, [0.42, 0.32, 0.24]);
        this.addBox(x - radius * 0.75, y - radius * 0.75, z + height * 0.35, radius * 1.5, radius * 1.5, height * 0.52, [0.96, 0.82, 0.16]);
      } else {
        // 도심 느티나무 및 일반 활엽수
        this.addPillar(x, y, z, z + height * 0.4, 0.8, [0.36, 0.25, 0.18]);
        this.addBox(x - radius, y - radius, z + height * 0.35, radius * 2, radius * 2, height * 0.45, [0.22, 0.60, 0.30]);
        this.addBox(x - radius * 0.75, y - radius * 0.75, z + height * 0.65, radius * 1.5, radius * 1.5, height * 0.35, [0.28, 0.70, 0.34]);
      }
    }"""

new_add_tree = """    // 초고화질 다층 수형 3D 가로수 및 조경수 (소나무, 벚나무, 수양버들, 은행나무, 느티나무, 관목)
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
    }"""

assert old_add_tree in content, "old_add_tree not found!"
content = content.replace(old_add_tree, new_add_tree)

with open(VIEW3D_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] addTree successfully upgraded in view3d.js")
