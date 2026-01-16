# -*- coding: utf-8 -*-
"""
Maya VAT - Utility Functions
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import json
import os


def get_mesh_fn(mesh_name):
    """Get MFnMesh from mesh name"""
    sel = om2.MSelectionList()
    sel.add(mesh_name)
    dag_path = sel.getDagPath(0)
    return om2.MFnMesh(dag_path)


def get_vertex_positions(mesh_name, use_world_space=True):
    """
    Get vertex positions as list of (x, y, z) tuples

    Args:
        mesh_name: Name of the mesh
        use_world_space: If True, use world space (kWorld).
                        If False, use object/local space (kObject).

    Returns:
        List of (x, y, z) tuples
    """
    mesh_fn = get_mesh_fn(mesh_name)
    space = om2.MSpace.kWorld if use_world_space else om2.MSpace.kObject
    points = mesh_fn.getPoints(space)
    return [(p.x, p.y, p.z) for p in points]


def get_vertex_normals(mesh_name):
    """Get vertex normals as list of (x, y, z) tuples (in object space)"""
    mesh_fn = get_mesh_fn(mesh_name)
    # Use object space so PlayCanvas can properly transform with matrix_normal
    normals = mesh_fn.getVertexNormals(False, om2.MSpace.kObject)
    return [(n.x, n.y, n.z) for n in normals]


def get_vertex_count(mesh_name):
    """Get number of vertices"""
    mesh_fn = get_mesh_fn(mesh_name)
    return mesh_fn.numVertices


def get_frame_range():
    """Get timeline frame range"""
    start = int(cmds.playbackOptions(q=True, min=True))
    end = int(cmds.playbackOptions(q=True, max=True))
    return start, end


def set_current_frame(frame):
    """Set current frame"""
    cmds.currentTime(frame, edit=True)


def get_current_frame():
    """Get current frame"""
    return int(cmds.currentTime(q=True))


def find_min_max(all_positions):
    """
    Find min/max values across all frames
    all_positions: dict {frame: [(x,y,z), ...]}
    Returns: (min_x, min_y, min_z, max_x, max_y, max_z)
    """
    min_vals = [float('inf'), float('inf'), float('inf')]
    max_vals = [float('-inf'), float('-inf'), float('-inf')]

    for frame, positions in all_positions.items():
        for pos in positions:
            for i in range(3):
                min_vals[i] = min(min_vals[i], pos[i])
                max_vals[i] = max(max_vals[i], pos[i])

    return (*min_vals, *max_vals)


def remap_value(value, old_min, old_max, new_min=0, new_max=255):
    """Remap value from one range to another"""
    if old_max == old_min:
        return new_min
    ratio = (value - old_min) / (old_max - old_min)
    return int(new_min + ratio * (new_max - new_min))


def write_json(data, filepath):
    """Write data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)


def ensure_directory(path):
    """Create directory if not exists"""
    if not os.path.exists(path):
        os.makedirs(path)


def get_uv_set_names(mesh_name):
    """Get list of UV set names for a mesh"""
    # Get shape node
    shapes = cmds.listRelatives(mesh_name, shapes=True, type='mesh')
    if not shapes:
        return []
    return cmds.polyUVSet(shapes[0], query=True, allUVSets=True) or []


def uv_set_exists(mesh_name, uv_set_name):
    """Check if a UV set exists on the mesh"""
    return uv_set_name in get_uv_set_names(mesh_name)


def create_vat_uv(mesh_name, num_verts, num_frames, uv_set_name='VAT_UV', force=False):
    """
    Create VAT UV set for mesh using Maya cmds (more stable)
    """
    # Get shape node
    shapes = cmds.listRelatives(mesh_name, shapes=True, type='mesh')
    if not shapes:
        raise ValueError("No mesh shape found for '{}'".format(mesh_name))

    shape_name = shapes[0]

    # Check if UV set already exists
    existing_sets = get_uv_set_names(mesh_name)

    if uv_set_name in existing_sets:
        if not force:
            print("VAT UV '{}' already exists, skipping".format(uv_set_name))
            return {'created': False, 'uv_set_name': uv_set_name, 'skipped': True}
        else:
            cmds.polyUVSet(shape_name, delete=True, uvSet=uv_set_name)
            print("Deleted existing UV set: '{}'".format(uv_set_name))

    # Get vertex count
    vertex_count = cmds.polyEvaluate(mesh_name, vertex=True)
    print("Creating VAT UV on: '{}', {} verts".format(mesh_name, vertex_count))

    # Pixel size
    pixel_size_u = 1.0 / vertex_count
    pixel_size_v = 1.0 / num_frames

    # 1. Create new UV set
    cmds.polyUVSet(shape_name, create=True, uvSet=uv_set_name)
    
    # 2. Set as current UV set (í•„ìˆ˜!)
    cmds.polyUVSet(shape_name, currentUVSet=True, uvSet=uv_set_name)
    
    # 3. Initialize UVs with planar projection (UV ì¢Œí‘œ ìƒì„±)
    cmds.polyProjection(
        '{}.f[*]'.format(mesh_name),
        type='Planar',
        mapDirection='y',
        uvSetName=uv_set_name
    )
    
    # 4. Now set each vertex UV to correct position
    for vtx_id in range(vertex_count):
        u = (vtx_id + 0.5) * pixel_size_u
        v = 0.5 * pixel_size_v
        
        # Get UV indices for this vertex in the UV set
        uv_indices = cmds.polyListComponentConversion(
            '{}.vtx[{}]'.format(mesh_name, vtx_id),
            fromVertex=True,
            toUV=True
        )
        if uv_indices:
            uv_indices = cmds.ls(uv_indices, flatten=True)
            for uv in uv_indices:
                cmds.polyEditUV(uv, relative=False, uValue=u, vValue=v)

    # 5. Restore map1 as current
    if 'map1' in get_uv_set_names(mesh_name):
        cmds.polyUVSet(shape_name, currentUVSet=True, uvSet='map1')

    print("VAT UV created: '{}' with {} verts, {} frames".format(
        uv_set_name, vertex_count, num_frames))

    return {'created': True, 'uv_set_name': uv_set_name, 'skipped': False}


def get_selected_mesh():
    """Get currently selected mesh"""
    sel = cmds.ls(selection=True, type='transform')
    if not sel:
        return None

    # Check if it has mesh shape
    shapes = cmds.listRelatives(sel[0], shapes=True, type='mesh')
    if shapes:
        return sel[0]
    return None