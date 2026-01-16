# Maya VAT Encoder
[![Maya](https://img.shields.io/badge/Maya-2022+-00B4FF?style=flat-square&logo=autodesk)](https://www.autodesk.com/products/maya)
[![Python](https://img.shields.io/badge/Python-Pure-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1.0-blue?style=flat-square)]()

**Maya용 Vertex Animation Texture 인코더** - 스킨메시, 디포머 등 움직이는 모든 것을 VAT로 변환해보세요!

![Demo](https://github.com/user-attachments/assets/e7b50f13-9a43-4ebe-9f14-aee65729311b)
<sub>*Astro Bot*™ © Sony Interactive Entertainment. Unofficial fan remake.</sub>

---

## 특징

- **의존성 없음** - 순수 Python, 추가 설치 불필요
- **Object/World Space** - 용도에 맞는 좌표계 선택
- **자동 VAT UV 생성** - 버텍스 ID 기반 UV 자동 할당
- **Skip First Frame** - T-Pose 제외 옵션
- **원클릭 출력** - PNG + JSON + FBX 일괄 생성

---

## 빠른 시작

```python
import maya_vat
maya_vat.show()
```

### 설치

1. `maya_vat` 폴더를 Maya 스크립트 경로에 복사
   ```
   # Windows
   C:/Users/<사용자>/Documents/maya/<버전>/scripts/

   # macOS
   ~/Library/Preferences/Autodesk/maya/<버전>/scripts/

   # Linux
   ~/maya/<버전>/scripts/
   ```

2. Maya 재시작 또는 Script Editor에서 위 코드 실행

### 출력 파일 구조

```
output_dir/
+-- mesh_vat/
    +-- mesh_vat.png       # Position 텍스처
    +-- mesh_vnrm.png      # Normal 텍스처 (선택)
    +-- mesh_remap.json    # 바운드 메타데이터
    +-- mesh.fbx           # 프록시 메시 (선택)
```

---
## 주요 옵션
![Image](https://github.com/user-attachments/assets/dd124ec8-42ee-4941-a186-06b7c061b25c)

### Coordinate Space

| 옵션 | 사용 상황 |
|------|-----------|
| **Object (Local)** | 런타임에 캐릭터 이동/회전 필요 **(권장)** |
| **World** | Transform 고정 (배경 오브젝트 등) |

### Skip First Frame

| 상황 | 설정 |
|------|------|
| 첫 프레임이 T-Pose/Bind Pose | **ON** |
| 첫 프레임부터 애니메이션 시작 | **OFF** |

---

## 워크플로우

```
[메시 선택] -> [프록시 캡처] -> [델타 계산] -> [VAT 출력]
                    |                              |
              첫 프레임 위치              PNG + JSON + FBX
```

### 텍스처 구조

```
Width  = 버텍스 수
Height = 프레임 수

        V0    V1    V2    V3   ...   Vn
      +-----+-----+-----+-----+---+-----+
  F0  | RGB | RGB | RGB | RGB |...| RGB |  <- Row 0
  F1  | RGB | RGB | RGB | RGB |...| RGB |  <- Row 1
  F2  | RGB | RGB | RGB | RGB |...| RGB |  <- Row 2
   :  |     |     |     |     |   |     |
      +-----+-----+-----+-----+---+-----+

픽셀 RGB = (deltaX, deltaY, deltaZ) normalized to 0-255
```

---

## 파일 구조

```
maya_vat/
+-- __init__.py      # 패키지 진입점
+-- core.py          # VAT 인코딩 로직
+-- utils.py         # Maya API 유틸리티
+-- exporter.py      # FBX/OBJ 내보내기
+-- ui.py            # PySide2/6 UI
+-- README.md
```

---

## 코드 API

### VAT 인코딩

```python
from maya_vat import core, utils

result = core.encode_vat(
    mesh_name="pCube1",
    output_dir="C:/output",
    frame_start=0,
    frame_end=60,
    include_normals=True,
    export_mesh=True,
    use_world_space=False,      # Object Space 권장
    uv_set_name="VAT_UV",
    force_uv=False,
    skip_first_frame=True       # T-Pose 제외
)

# 반환값
# {
#     "success": True,
#     "png_path": "C:/output/pCube1_vat/pCube1_vat.png",
#     "json_path": "C:/output/pCube1_vat/pCube1_remap.json",
#     "fbx_path": "C:/output/pCube1_vat/pCube1.fbx",
#     "width": 8,
#     "height": 60,
#     ...
# }
```

### VAT UV 독립 생성

```python
uv_result = utils.create_vat_uv(
    mesh_name="pCube1",
    num_verts=1024,
    num_frames=60,
    uv_set_name="VAT_UV",
    force=False  # 존재하면 스킵
)

# UV 세트 존재 확인
exists = utils.uv_set_exists("pCube1", "VAT_UV")
```

### JSON 메타데이터

```json
{
    "position": {
        "min": [-2.5, -1.0, -0.5],
        "max": [3.2, 4.5, 1.2],
        "frames": 60,
        "vertices": 1024,
        "space": "object"
    },
    "normal": {
        "min": [-1, -1, -1],
        "max": [1, 1, 1]
    }
}
```

---

## 주의사항

### Object Space vs World Space

| 상황 | Object | World |
|------|:------:|:-----:|
| 런타임 이동/회전 | O | X |
| 루트 모션 애니메이션 | O | X (중복 이동) |
| Transform 고정 | O | O |

### UV 세트

- 기존 UV 세트와 이름 충돌 주의
- `Overwrite if exists` 체크 시 기존 UV 삭제 후 재생성
- UV Editor > UV Sets에서 확인 가능

### FBX 내보내기

- 스킨/본 제외 (VAT는 스킨 불필요)
- 블렌드쉐입 제외
- 애니메이션 제외 (첫 프레임만)

---

## License

MIT License

---

**Contact:** 555hyuns@gmail.com
