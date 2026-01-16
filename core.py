# -*- coding: utf-8 -*-
"""
Maya VAT - Core VAT Encoding Logic
"""

import maya.cmds as cmds
import os
import struct
import zlib

from . import utils


def encode_vat(mesh_name, output_dir, frame_start=None, frame_end=None,
               include_normals=False, export_mesh=True, use_world_space=True,
               uv_set_name='VAT_UV', force_uv=False, skip_first_frame=False):
    """
    Main VAT encoding function

    Args:
        mesh_name: Name of the mesh to encode
        output_dir: Output directory path
        frame_start: Start frame (default: timeline start)
        frame_end: End frame (default: timeline end)
        include_normals: Whether to create separate normal texture
        export_mesh: Whether to export FBX
        use_world_space: If True, use world space (kWorld).
                        If False, use object/local space (kObject).
                        Recommended: False for characters with runtime movement.
        uv_set_name: Name of the VAT UV set (default: VAT_UV)
        force_uv: If True, overwrite existing UV set. If False, skip if exists.
        skip_first_frame: If True, use first frame only as proxy reference.
                         The first frame will NOT be included in the texture.
                         Useful when first frame is T-Pose or bind pose.

    Returns:
        dict with results info
    """
    # Validate mesh
    if not cmds.objExists(mesh_name):
        raise ValueError("Mesh '{}' not found".format(mesh_name))

    # Get frame range
    if frame_start is None or frame_end is None:
        fs, fe = utils.get_frame_range()
        frame_start = frame_start or fs
        frame_end = frame_end or fe

    total_frames = frame_end - frame_start + 1
    num_verts = utils.get_vertex_count(mesh_name)

    # Validate skip_first_frame
    if skip_first_frame and total_frames < 2:
        raise ValueError("Skip First Frame requires at least 2 frames")

    # Texture frames (exclude first frame if skip_first_frame)
    num_frames = total_frames - 1 if skip_first_frame else total_frames
    texture_start_frame = frame_start + 1 if skip_first_frame else frame_start

    # Create output directory
    base_name = mesh_name.replace(':', '_').replace('|', '_')
    object_dir = os.path.join(output_dir, "{}_vat".format(base_name))
    utils.ensure_directory(object_dir)

    # Store original frame
    original_frame = utils.get_current_frame()

    # Step 1: Get proxy positions (first frame)
    utils.set_current_frame(frame_start)
    proxy_positions = utils.get_vertex_positions(mesh_name, use_world_space)

    # Step 2: Collect all frame positions and calculate deltas
    all_deltas = {}
    all_normals = {} if include_normals else None

    for frame in range(frame_start, frame_end + 1):
        utils.set_current_frame(frame)
        positions = utils.get_vertex_positions(mesh_name, use_world_space)

        # Calculate delta from proxy
        deltas = []
        for i, pos in enumerate(positions):
            delta = (
                pos[0] - proxy_positions[i][0],
                pos[1] - proxy_positions[i][1],
                pos[2] - proxy_positions[i][2]
            )
            deltas.append(delta)

        all_deltas[frame] = deltas

        if include_normals:
            all_normals[frame] = utils.get_vertex_normals(mesh_name)

    # Step 3: Find min/max for remapping
    min_x, min_y, min_z, max_x, max_y, max_z = utils.find_min_max(all_deltas)

    # Step 4: Create image data (width=num_verts, height=num_frames)
    width = num_verts
    height = num_frames

    # RGB image data
    image_data = []

    # Start from texture_start_frame (skips first frame if skip_first_frame is True)
    for frame in range(texture_start_frame, frame_end + 1):
        row = []
        deltas = all_deltas[frame]

        for delta in deltas:
            r = utils.remap_value(delta[0], min_x, max_x, 0, 255)
            g = utils.remap_value(delta[1], min_y, max_y, 0, 255)
            b = utils.remap_value(delta[2], min_z, max_z, 0, 255)
            row.append((r, g, b))

        image_data.append(row)

    # Step 5: Save PNG
    png_path = os.path.join(object_dir, "{}_vat.png".format(base_name))
    save_png(image_data, width, height, png_path)

    # Step 6: Save normal texture if needed
    if include_normals:
        normal_image_data = []
        # Start from texture_start_frame (same as position texture)
        for frame in range(texture_start_frame, frame_end + 1):
            row = []
            normals = all_normals[frame]
            for normal in normals:
                # Normals are -1 to 1, remap to 0-255
                # Flip X axis for PlayCanvas compatibility
                r = utils.remap_value(-normal[0], -1, 1, 0, 255)
                g = utils.remap_value(normal[1], -1, 1, 0, 255)
                b = utils.remap_value(normal[2], -1, 1, 0, 255)
                row.append((r, g, b))
            normal_image_data.append(row)

        normal_png_path = os.path.join(object_dir, "{}_vnrm.png".format(base_name))
        save_png(normal_image_data, width, height, normal_png_path)

    # Step 7: Save JSON metadata
    json_data = {
        "position": {
            "min": [min_x, min_y, min_z],
            "max": [max_x, max_y, max_z],
            "frames": num_frames,
            "vertices": num_verts,
            "space": "world" if use_world_space else "object"
        }
    }

    if include_normals:
        json_data["normal"] = {
            "min": [-1, -1, -1],
            "max": [1, 1, 1]
        }

    json_path = os.path.join(object_dir, "{}_remap.json".format(base_name))
    utils.write_json(json_data, json_path)

    # Step 8: Create VAT UV
    uv_result = utils.create_vat_uv(mesh_name, num_verts, num_frames, uv_set_name, force_uv)

    # Step 9: Export mesh if requested
    fbx_path = None
    if export_mesh:
        # Set frame to frame_start for correct proxy mesh pose
        utils.set_current_frame(frame_start)
        from . import exporter
        fbx_path = exporter.export_fbx(mesh_name, object_dir, base_name)

    # Restore original frame
    utils.set_current_frame(original_frame)

    return {
        "success": True,
        "png_path": png_path,
        "json_path": json_path,
        "fbx_path": fbx_path,
        "width": width,
        "height": height,
        "num_verts": num_verts,
        "num_frames": num_frames,
        "total_frames": total_frames,
        "skip_first_frame": skip_first_frame,
        "space": "world" if use_world_space else "object",
        "uv_set_name": uv_set_name,
        "uv_created": uv_result.get('created', False),
        "uv_skipped": uv_result.get('skipped', False)
    }


def save_png(image_data, width, height, filepath):
    """
    Save image data as PNG (pure Python, no external dependencies)

    Args:
        image_data: 2D list of (R, G, B) tuples
        width: Image width
        height: Image height
        filepath: Output path
    """
    def write_chunk(f, chunk_type, data):
        """Write PNG chunk"""
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xffffffff
        f.write(struct.pack('>I', len(data)))
        f.write(chunk)
        f.write(struct.pack('>I', crc))

    with open(filepath, 'wb') as f:
        # PNG signature
        f.write(b'\x89PNG\r\n\x1a\n')

        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        write_chunk(f, b'IHDR', ihdr_data)

        # IDAT chunk (image data)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'  # Filter type: None
            for x in range(width):
                r, g, b = image_data[y][x]
                raw_data += struct.pack('BBB', r, g, b)

        compressed = zlib.compress(raw_data, 9)
        write_chunk(f, b'IDAT', compressed)

        # IEND chunk
        write_chunk(f, b'IEND', b'')
