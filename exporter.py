# -*- coding: utf-8 -*-
"""
Maya VAT - Mesh Exporter
"""

import maya.cmds as cmds
import maya.mel as mel
import os


def ensure_fbx_plugin():
    """Load FBX plugin if not loaded"""
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        try:
            cmds.loadPlugin('fbxmaya')
        except:
            raise RuntimeError("FBX plugin not available")


def export_fbx(mesh_name, output_dir, base_name=None):
    """
    Export mesh as FBX with VAT UV

    Args:
        mesh_name: Name of mesh to export
        output_dir: Output directory
        base_name: Base name for file (default: mesh_name)

    Returns:
        Path to exported FBX file
    """
    # Ensure FBX plugin is loaded
    ensure_fbx_plugin()

    if base_name is None:
        base_name = mesh_name.replace(':', '_').replace('|', '_')

    fbx_path = os.path.join(output_dir, "{}.fbx".format(base_name))

    # Store selection
    original_sel = cmds.ls(selection=True)

    # Select mesh
    cmds.select(mesh_name, replace=True)

    # FBX export settings
    mel.eval('FBXResetExport')

    # Basic settings
    mel.eval('FBXExportSmoothingGroups -v true')
    mel.eval('FBXExportSmoothMesh -v false')
    mel.eval('FBXExportTangents -v true')
    mel.eval('FBXExportSkins -v false')
    mel.eval('FBXExportShapes -v false')
    mel.eval('FBXExportCameras -v false')
    mel.eval('FBXExportLights -v false')
    mel.eval('FBXExportEmbeddedTextures -v false')
    mel.eval('FBXExportInputConnections -v false')
    mel.eval('FBXExportUseSceneName -v false')
    mel.eval('FBXExportInAscii -v false')

    # Animation off
    mel.eval('FBXExportBakeComplexAnimation -v false')
    mel.eval('FBXExportAnimationOnly -v false')
    mel.eval('FBXExportApplyConstantKeyReducer -v false')

    # Export selected only
    mel.eval('FBXExport -f "{}" -s'.format(fbx_path.replace('\\', '/')))

    # Restore selection
    if original_sel:
        cmds.select(original_sel, replace=True)
    else:
        cmds.select(clear=True)

    return fbx_path


def export_obj(mesh_name, output_dir, base_name=None):
    """
    Export mesh as OBJ (alternative to FBX)

    Args:
        mesh_name: Name of mesh to export
        output_dir: Output directory
        base_name: Base name for file

    Returns:
        Path to exported OBJ file
    """
    if base_name is None:
        base_name = mesh_name.replace(':', '_').replace('|', '_')

    obj_path = os.path.join(output_dir, "{}.obj".format(base_name))

    # Store selection
    original_sel = cmds.ls(selection=True)

    # Select mesh
    cmds.select(mesh_name, replace=True)

    # Export OBJ
    cmds.file(
        obj_path,
        force=True,
        options="groups=1;ptgroups=1;materials=0;smoothing=1;normals=1",
        type="OBJexport",
        exportSelected=True
    )

    # Restore selection
    if original_sel:
        cmds.select(original_sel, replace=True)
    else:
        cmds.select(clear=True)

    return obj_path
