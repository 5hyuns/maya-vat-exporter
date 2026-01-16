# -*- coding: utf-8 -*-
"""
Maya VAT - Vertex Animation Texture Encoder

A Maya tool for encoding vertex animation textures for real-time engines.

Usage:
    import maya_openvat
    maya_openvat.show()

Author: 555hyuns@gmail.com
Version: 1.1.0
"""

__version__ = "1.1.0"
__author__ = "555hyuns@gmail.com"

from .ui import show
from .core import encode_vat

__all__ = ['show', 'encode_vat']
