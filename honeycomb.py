
# BSD 3-Clause License
#
# Copyright (c) 2025, Viktor Samokhin (wowyupiyo@gmail.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
################################################################################
#
# v0.0.1
# Honeycomb infill pattern generator

import cadquery as cq
from cadquery import Workplane
import math


def _hex_centers(width, height, cell_size):
    """
    Generate (x,y) centers for hex grid covering bounding box
    """
    hex_height = math.sqrt(3) * cell_size
    x_step = 1.5 * cell_size
    y_step = hex_height
    xmin = -width / 2 - cell_size
    xmax = width / 2 + cell_size
    ymin = -height / 2 - cell_size
    ymax = height / 2 + cell_size

    x = xmin
    col = 0
    while x <= xmax:
        y_offset = (hex_height / 2) if (col % 2 == 1) else 0.0
        y = ymin + y_offset
        while y <= ymax:
            yield (x, y)
            y += y_step
        x += x_step
        col += 1

def _hex_ring(center, cell_size, edge_width, thickness):
    """
    Return a 3D hex 'ring' solid centered at (x,y)
    """
    x, y = center
    wp = cq.Workplane("XY").center(x, y)
    outer = wp.polygon(6, 2 * cell_size).extrude(thickness)
    inner_r = max(cell_size - edge_width / 2.0, 0)
    if inner_r > 0:
        inner = cq.Workplane("XY").center(x, y).polygon(6, 2 * inner_r).extrude(thickness)
        ring = outer.cut(inner)
    else:
        ring = outer
    return ring

def _honeycomb_grid(width, height, cell_size, edge_width, thickness):
    """
    Union of all hex rings covering a bounding box
    """
    result = cq.Workplane("XY")
    for c in _hex_centers(width, height, cell_size):
        result = result.union(_hex_ring(c, cell_size, edge_width, thickness))
    return result

def apply_honeycomb(wall: Workplane, cell_size, edge_width, shell_thickness, normal_axis='Z') -> Workplane:
    """
    Apply a honeycomb infill to any polygonal wall solid
    """
    solid = wall.val()
    bb = solid.BoundingBox() # pyright: ignore[reportAttributeAccessIssue]
    width, height, thickness = bb.xlen, bb.ylen, bb.zlen

    # Determine the wall's base plane (assume built on XY)
    base_z = bb.zmin
    cx, cy = (bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2

    # Create the outer shell
    shell_only = wall.faces(f"+{normal_axis} or -{normal_axis}").shell(shell_thickness, kind='intersection')

    # Build honeycomb grid aligned to wall center
    pattern = _honeycomb_grid(width, height, cell_size, edge_width, thickness)
    pattern = pattern.translate((cx, cy, base_z))

    # Intersect pattern with the fill region and wall
    infill = wall.intersect(pattern)

    return shell_only.union(infill)
