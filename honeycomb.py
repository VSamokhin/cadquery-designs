
import cadquery as cq
from cadquery import Workplane
from typing import TypeVar
import math


def hex_center_points(width, height, cell_size):
    """
    Yield (x,y) centers to cover bounding box of given width/height.
    cell_size = distance center->vertex (circumradius)
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


def make_hexagon_solid(center, radius, thickness_z):
    """
    Return a Workplane solid: regular hexagon extruded to thickness_z.
    """
    x, y = center
    wp = cq.Workplane("XY").center(x, y).polygon(6, 2 * radius).extrude(thickness_z)
    return wp


def honeycomb_pattern_solid(width, height, cell_size, wall_width, thickness_z):
    """
    Make a honeycomb lattice solid covering a bounding box.
    """
    inner_radius = max(cell_size - wall_width, 0)
    make_hole = inner_radius > 0
    pattern = cq.Workplane("XY")

    for center in hex_center_points(width, height, cell_size):
        outer = make_hexagon_solid(center, cell_size, thickness_z)
        if make_hole:
            inner = make_hexagon_solid(center, inner_radius, thickness_z)
            ring = outer.cut(inner)
        else:
            ring = outer
        pattern = pattern.union(ring)

    return pattern

T = TypeVar("T", bound="Workplane")

def apply_honeycomb_to_shape(shape, cell_size, edge_width, keep_shell):
    """
    Apply honeycomb infill to a solid wall (CadQuery 2.5.2 compatible).
    """
    # Make sure we have a solid to inspect
    solid = shape.val()  # first solid in Workplane
    bb = solid.BoundingBox()
    width, height, thickness_z = bb.xlen, bb.ylen, bb.zlen

    # build fill region — optionally inset by keep_shell
    # top face selection
    top_face = shape.faces(">Z")
    if keep_shell > 0:
        try:
            inset_2d = top_face.workplane().offset2D(-keep_shell)
            fill_region = inset_2d.extrude(thickness_z)
        except Exception:
            # fallback if offset2D fails
            fill_region = cq.Workplane("XY").rect(width - 2 * keep_shell, height - 2 * keep_shell).extrude(thickness_z)
    else:
        fill_region = shape

    # Create honeycomb pattern matching bounding box
    pattern = honeycomb_pattern_solid(width, height, cell_size, edge_width, thickness_z)

    # Move pattern to match shape's bounding box center
    cx = (bb.xmin + bb.xmax) / 2
    cy = (bb.ymin + bb.ymax) / 2
    cz = bb.zmin
    pattern = pattern.translate((cx, cy, cz))

    # Intersect pattern with fill region, then intersect with shape
    infill = pattern.intersect(fill_region).intersect(shape)

    if keep_shell > 0:
        shell = shape.cut(fill_region)
        result = shell.union(infill)
    else:
        result = infill

    return result