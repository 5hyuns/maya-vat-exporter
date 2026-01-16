# Maya VAT Encoder
[![Maya](https://img.shields.io/badge/Maya-2022+-00B4FF?style=flat-square&logo=autodesk)](https://www.autodesk.com/products/maya)
[![Python](https://img.shields.io/badge/Python-Pure-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1.0-blue?style=flat-square)]()

🌐 English | [한국어](README.ko.md)

**Vertex Animation Texture Encoder for Maya** - Convert skinned meshes, deformers, and anything that moves into VAT!

![Demo](https://github.com/user-attachments/assets/e7b50f13-9a43-4ebe-9f14-aee65729311b)
<sub>*Astro Bot*™ © Sony Interactive Entertainment. Unofficial fan remake.</sub>

---

## Features

- **Zero Dependencies** - Pure Python, no additional installation required
- **Object/World Space** - Choose coordinate space for your needs
- **Auto VAT UV Generation** - Automatic UV assignment based on vertex ID
- **Skip First Frame** - Option to exclude T-Pose
- **One-Click Export** - Batch generation of PNG + JSON + FBX

---

## Quick Start
```python
import maya_vat
maya_vat.show()
```

### Installation

1. Copy the `maya_vat` folder to your Maya scripts path
```
   # Windows
   C:/Users/<username>/Documents/maya/<version>/scripts/

   # macOS
   ~/Library/Preferences/Autodesk/maya/<version>/scripts/

   # Linux
   ~/maya/<version>/scripts/
```

2. Restart Maya or run the code above in Script Editor

### Output File Structure
```
output_dir/
+-- mesh_vat/
    +-- mesh_vat.png       # Position texture
    +-- mesh_vnrm.png      # Normal texture (optional)
    +-- mesh_remap.json    # Bounding box metadata
    +-- mesh.fbx           # Proxy mesh (optional)
```

---

## Main Options
![Image](https://github.com/user-attachments/assets/dd124ec8-42ee-4941-a186-06b7c061b25c)

### Coordinate Space

| Option | Use Case |
|--------|----------|
| **Object (Local)** | Character needs runtime movement/rotation **(Recommended)** |
| **World** | Fixed transform (background objects, etc.) |

### Skip First Frame

| Situation | Setting |
|-----------|---------|
| First frame is T-Pose/Bind Pose | **ON** |
| Animation starts from first frame | **OFF** |

---

## Workflow
```
[Select Mesh] -> [Bake Proxy] -> [Compute Deltas] -> [Export VAT]
                      |                                    |
                First frame position             PNG + JSON + FBX
```

### Texture Structure
```
Width  = Number of vertices
Height = Number of frames

        V0    V1    V2    V3   ...   Vn
      +-----+-----+-----+-----+---+-----+
  F0  | RGB | RGB | RGB | RGB |...| RGB |  <- Row 0
  F1  | RGB | RGB | RGB | RGB |...| RGB |  <- Row 1
  F2  | RGB | RGB | RGB | RGB |...| RGB |  <- Row 2
   :  |     |     |     |     |   |     |
      +-----+-----+-----+-----+---+-----+

Pixel RGB = (deltaX, deltaY, deltaZ) normalized to 0-255
```

---

## File Structure
```
maya_vat/
+-- __init__.py      # Package entry point
+-- core.py          # VAT encoding logic
+-- utils.py         # Maya API utilities
+-- exporter.py      # FBX/OBJ export
+-- ui.py            # PySide2/6 UI
+-- README.md
```

---

## Code API

### VAT Encoding
```python
from maya_vat import core, utils

result = core.encode_vat(
    mesh_name="pCube1",
    output_dir="C:/output",
    frame_start=0,
    frame_end=60,
    include_normals=True,
    export_mesh=True,
    use_world_space=False,      # Object Space recommended
    uv_set_name="VAT_UV",
    force_uv=False,
    skip_first_frame=True       # Exclude T-Pose
)

# Returns
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

### Standalone VAT UV Generation
```python
uv_result = utils.create_vat_uv(
    mesh_name="pCube1",
    num_verts=1024,
    num_frames=60,
    uv_set_name="VAT_UV",
    force=False  # Skip if exists
)

# Check if UV set exists
exists = utils.uv_set_exists("pCube1", "VAT_UV")
```

### JSON Metadata
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

## Notes

### Object Space vs World Space

| Situation | Object | World |
|-----------|:------:|:-----:|
| Runtime movement/rotation | O | X |
| Root motion animation | O | X (double transformation) |
| Fixed transform | O | O |

### UV Sets

- Avoid name conflicts with existing UV sets
- Checking `Overwrite if exists` deletes and regenerates existing UV
- Verify in UV Editor > UV Sets

### FBX Export

- Skinning-free (VAT replaces skeletal deformation)
- Excludes blend shapes
- Excludes animation (first frame only)

---

## License

MIT License

---

**Contact:** 555hyuns@gmail.com
