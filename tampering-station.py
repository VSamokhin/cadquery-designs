# BSD 3-Clause License
#
# Copyright (c) 2026, Viktor Samokhin (wowyupiyo@gmail.com)
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
# Home baristas' best friend, a tampering station with some additional slots
# to store tools and accessories like leveler, tamper, screens, porta filters, etc.
# My work is inspired by https://www.printables.com/model/773844-heavy-tamperstation

from functools import reduce
import cq_utils
import math
import cadquery as cq
from cadquery.selectors import StringSyntaxSelector
from cadquery.selectors import BoxSelector


# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False

# Configuration (tweak if needed)
MARGIN = 10.0

PORTA_HOLDER_DIAMETER = 74.0
PORTA_HOLDER_DEPTH_Z = 75.0 # Z
PORTA_HANDLE_LENGTH_Y = 15.0 # Y
PORTA_HANDLE_WIDTH_X = 25.0 # X
PORTA_HANDLE_DEPTH_Z = 45.0 # Z
PORTA_HANDLE_SCREW_DIAMETER = 4.0
PORTA_HANDLE_SCREW_DEPTH_Z = 15.0 # Z

UPPER_LEFT_DIAMETER = 60.0
UPPER_LEFT_DEPTH_Z = 15.0

UPPER_MIDDLE_LENGTH_X = 50.0
UPPER_MIDDLE_WIDTH_Y = 35.0
UPPER_MIDDLE_DEPTH_Z = 35.0

UPPER_RIGHT_DIAMETER = 60.0
UPPER_RIGHT_DEPTH_Z = 15.0

LOWER_LEFT_SLOT_WIDTH_X = 3.0 # X
LOWER_LEFT_SLOT_LENGTH_Y = 50.0 # Y
LOWER_LEFT_SLOT_GAP = 5.0
LOWER_LEFT_SLOT_COUNT = 3
LOWER_LEFT_HOLE_DIAMETER = 25.0
LOWER_LEFT_DEPTH_Z = 15.0 # Z

LOWER_RIGHT_DIAMETER = 40.0
LOWER_RIGHT_DEPTH_Z = 35.0

INTERNAL_WALL = 5.0

CORNERS_FILLET_RADIUS = 15.0
CUTOUT_FILLET_RADIUS = 1.0
BOTTOM_FILLET_RADIUS = 1.0
TOP_FILLET_RADIUS = 2.2
DRAWER_FILLET_RADIUS = 1.5
DRAWER_CHAMFER_LENGTH = 10.0
DRAWER_CHAMFER_FILLET_RADIUS = 10.0

# Derived dimensions, don't change
LOWER_LEFT_SLOTS_WIDTH_X = LOWER_LEFT_SLOT_COUNT * LOWER_LEFT_SLOT_WIDTH_X + (LOWER_LEFT_SLOT_COUNT - 1) * LOWER_LEFT_SLOT_GAP
LENGTH_X = MARGIN + max(UPPER_LEFT_DIAMETER, LOWER_LEFT_SLOTS_WIDTH_X + MARGIN, + LOWER_LEFT_HOLE_DIAMETER) + PORTA_HOLDER_DIAMETER + max(UPPER_RIGHT_DIAMETER, LOWER_RIGHT_DIAMETER) + MARGIN # X
WIDTH_Y = PORTA_HANDLE_LENGTH_Y + PORTA_HOLDER_DIAMETER + MARGIN + UPPER_MIDDLE_WIDTH_Y + MARGIN # Y
HEIGHT_Z = PORTA_HOLDER_DEPTH_Z + INTERNAL_WALL # Z

DRAWER_WIDTH_Y = WIDTH_Y - CORNERS_FILLET_RADIUS * 2.0 - MARGIN * 2.0 # Y
DRAWER_HEIGHT_Z = HEIGHT_Z - max(UPPER_LEFT_DEPTH_Z, UPPER_RIGHT_DEPTH_Z, LOWER_LEFT_DEPTH_Z, LOWER_RIGHT_DEPTH_Z) - 2 * INTERNAL_WALL # Z
DRAWER_DEPTH_X = (LENGTH_X - 2 * INTERNAL_WALL - PORTA_HOLDER_DIAMETER) / 2.0 # X

# Sanity checks
assert (MARGIN + UPPER_LEFT_DIAMETER
        + MARGIN + UPPER_MIDDLE_LENGTH_X
        + MARGIN + UPPER_RIGHT_DIAMETER + MARGIN < LENGTH_X), "Wrong upper X dimensions!"
assert (MARGIN + LOWER_LEFT_SLOTS_WIDTH_X
        + MARGIN + LOWER_LEFT_HOLE_DIAMETER
        + MARGIN + PORTA_HOLDER_DIAMETER
        + MARGIN + LOWER_RIGHT_DIAMETER + MARGIN <= LENGTH_X), "Wrong lower left X dimensions!"
assert MARGIN + UPPER_LEFT_DIAMETER + MARGIN + LOWER_LEFT_SLOT_LENGTH_Y + MARGIN <= WIDTH_Y, "Wrong Y dimensions!"
assert PORTA_HANDLE_DEPTH_Z + PORTA_HANDLE_SCREW_DEPTH_Z + INTERNAL_WALL < HEIGHT_Z, "Wrong handle Z dimensions!"

type Vertex = tuple[float, float, float]

def bbox(center: Vertex, size_x: float, size_y: float, size_z: float, z_offset: float, extension: float = 1.0) -> tuple[Vertex, Vertex]:
    """Define a 3D bounding box for a given on the upper plane center"""
    half_x = size_x / 2.0
    half_y = size_y / 2.0
    return ((center[0] - half_x - extension, center[1] - half_y - extension, z_offset + center[2] - size_z - extension),
            (center[0] + half_x + extension, center[1] + half_y + extension, z_offset + center[2] + extension))

def extend_bbox(bbox: tuple[Vertex, Vertex], ext_x: float, ext_y: float, ext_z: float) -> tuple[Vertex, Vertex]:
    """Extend a bounding box by a given amount in all directions"""
    min_pt, max_pt = bbox
    half_ext_x = ext_x / 2.0
    half_ext_y = ext_y / 2.0
    half_ext_z = ext_z / 2.0
    return ((min_pt[0] - half_ext_x, min_pt[1] - half_ext_y, min_pt[2] - half_ext_z),
            (max_pt[0] + half_ext_x, max_pt[1] + half_ext_y, max_pt[2] + half_ext_z))

def calculate_shift(diameter: float, rect_width: float):
    """
    Calculate distance to shift rectangle along axis so its corners touch the circle.

    Args:
        diameter: Circle diameter
        rect_width: Rectangle width (side perpendicular to axis)
    Returns:
        Shift distance along axis (positive = toward circle center)
    """
    r = diameter / 2
    half_width = rect_width / 2

    # Distance from circle center to corner when corner is on circle
    # Using Pythagorean theorem: r² = x² + (half_width)²
    x = math.sqrt(r**2 - half_width**2)

    # Shift needed (positive = move toward center)
    return r - x

def create_box(bbox: tuple[Vertex, Vertex]) -> cq.Workplane:
    """
    Create a box from bounding box coordinates.
    Basically this is a debug helper to visualize bounding boxes.
    """
    min_pt, max_pt = bbox
    size_x = max_pt[0] - min_pt[0]
    size_y = max_pt[1] - min_pt[1]
    size_z = max_pt[2] - min_pt[2]
    center_x = (min_pt[0] + max_pt[0]) / 2.0
    center_y = (min_pt[1] + max_pt[1]) / 2.0
    center_z = (min_pt[2] + max_pt[2]) / 2.0
    return (cq
        .Workplane("XY")
        .box(size_x, size_y, size_z)
        .translate((center_x, center_y, center_z))
    )

if __name__ == "__main__":
    # Calculate positions and bounding boxes
    upper_left_origin = (-LENGTH_X / 2.0 + MARGIN + UPPER_LEFT_DIAMETER / 2.0, WIDTH_Y / 2.0 - MARGIN - UPPER_LEFT_DIAMETER / 2.0, 0.0)
    upper_left_bbox = bbox(upper_left_origin, UPPER_LEFT_DIAMETER, UPPER_LEFT_DIAMETER, UPPER_LEFT_DEPTH_Z, HEIGHT_Z / 2.0)

    upper_middle_origin = (0.0, WIDTH_Y / 2.0 - MARGIN - UPPER_MIDDLE_WIDTH_Y / 2.0, 0.0)
    upper_middle_bbox = bbox(upper_middle_origin, UPPER_MIDDLE_LENGTH_X, UPPER_MIDDLE_WIDTH_Y, UPPER_MIDDLE_DEPTH_Z, HEIGHT_Z / 2.0)

    upper_right_origin = (LENGTH_X / 2.0 - MARGIN - UPPER_RIGHT_DIAMETER / 2.0, WIDTH_Y / 2.0 - MARGIN - UPPER_RIGHT_DIAMETER / 2.0, 0.0)
    upper_right_bbox = bbox(upper_right_origin, UPPER_RIGHT_DIAMETER, UPPER_RIGHT_DIAMETER, UPPER_RIGHT_DEPTH_Z, HEIGHT_Z / 2.0)

    lower_left_slots_origin = (-LENGTH_X / 2.0 + MARGIN, (-WIDTH_Y + LOWER_LEFT_SLOT_LENGTH_Y) / 2.0 + MARGIN, 0.0)
    lower_left_slots_points = [((x * LOWER_LEFT_SLOT_WIDTH_X + (x - 1) * LOWER_LEFT_SLOT_GAP), 0.0) for x in range(1, LOWER_LEFT_SLOT_COUNT + 1)]
    lower_left_slots_bbox = bbox((lower_left_slots_origin[0] + (LOWER_LEFT_SLOT_WIDTH_X + LOWER_LEFT_SLOTS_WIDTH_X) / 2.0, lower_left_slots_origin[1], lower_left_slots_origin[2]),
                                LOWER_LEFT_SLOTS_WIDTH_X,
                                LOWER_LEFT_SLOT_LENGTH_Y,
                                LOWER_LEFT_DEPTH_Z,
                                HEIGHT_Z / 2.0)
    lower_left_hole_origin = (lower_left_slots_origin[0] + LOWER_LEFT_SLOTS_WIDTH_X + MARGIN + LOWER_LEFT_HOLE_DIAMETER / 2.0, (-WIDTH_Y + LOWER_LEFT_HOLE_DIAMETER) / 2.0 + MARGIN, 0.0)
    lower_left_hole_bbox = bbox(lower_left_hole_origin, LOWER_LEFT_HOLE_DIAMETER, LOWER_LEFT_HOLE_DIAMETER, LOWER_LEFT_DEPTH_Z, HEIGHT_Z / 2.0)

    lower_right_origin = (LENGTH_X / 2.0 - MARGIN - LOWER_RIGHT_DIAMETER / 2.0, -WIDTH_Y / 2.0 + MARGIN + LOWER_RIGHT_DIAMETER / 2.0, 0.0)
    lower_right_bbox = bbox(lower_right_origin, LOWER_RIGHT_DIAMETER, LOWER_RIGHT_DIAMETER, LOWER_RIGHT_DEPTH_Z, HEIGHT_Z / 2.0)

    porta_filter_origin = (0.0, -WIDTH_Y / 2.0 + PORTA_HOLDER_DIAMETER / 2.0 + PORTA_HANDLE_LENGTH_Y, 0.0)
    porta_filter_bbox = bbox(porta_filter_origin, PORTA_HOLDER_DIAMETER, PORTA_HOLDER_DIAMETER, PORTA_HOLDER_DEPTH_Z, HEIGHT_Z / 2.0)

    porta_handle_length_increased = PORTA_HANDLE_LENGTH_Y + calculate_shift(PORTA_HOLDER_DIAMETER, PORTA_HANDLE_WIDTH_X)
    porta_handle_origin = (0.0, (-WIDTH_Y + porta_handle_length_increased) / 2.0, 0.0)
    porta_handle_bbox = bbox(porta_handle_origin, PORTA_HANDLE_WIDTH_X, porta_handle_length_increased, PORTA_HANDLE_DEPTH_Z, HEIGHT_Z / 2.0)

    new_drawer_height_z = DRAWER_HEIGHT_Z + DRAWER_CHAMFER_LENGTH

    left_drawer_origin = (0.0, 0.0, -HEIGHT_Z / 2.0 + INTERNAL_WALL + DRAWER_HEIGHT_Z / 2.0)
    left_drawer_bbox = bbox(((-LENGTH_X + DRAWER_DEPTH_X) / 2.0, left_drawer_origin[1], new_drawer_height_z / 2.0),
                            DRAWER_DEPTH_X,
                            DRAWER_WIDTH_Y,
                            new_drawer_height_z,
                            left_drawer_origin[2] + DRAWER_CHAMFER_LENGTH / 2.0)
    left_drawer_chamfer_origin = ((-LENGTH_X + DRAWER_CHAMFER_LENGTH) / 2.0,
                           left_drawer_origin[1],
                           left_drawer_origin[2] + DRAWER_CHAMFER_LENGTH / 2.0)
    left_drawer_chamfer_bbox = bbox(left_drawer_chamfer_origin,
                             DRAWER_CHAMFER_LENGTH,
                             DRAWER_WIDTH_Y,
                             DRAWER_CHAMFER_LENGTH,
                             left_drawer_chamfer_origin[2] + DRAWER_HEIGHT_Z)

    right_drawer_origin = left_drawer_origin
    right_drawer_bbox = bbox(((LENGTH_X - DRAWER_DEPTH_X) / 2.0, right_drawer_origin[1], new_drawer_height_z / 2.0),
                             DRAWER_DEPTH_X,
                             DRAWER_WIDTH_Y,
                             new_drawer_height_z,
                             right_drawer_origin[2] + DRAWER_CHAMFER_LENGTH / 2.0)
    right_drawer_chamfer_origin = ((LENGTH_X - DRAWER_CHAMFER_LENGTH) / 2.0,
                           right_drawer_origin[1],
                           right_drawer_origin[2] + DRAWER_CHAMFER_LENGTH / 2.0)
    right_drawer_chamfer_bbox = bbox(right_drawer_chamfer_origin,
                             DRAWER_CHAMFER_LENGTH,
                             DRAWER_WIDTH_Y,
                             DRAWER_CHAMFER_LENGTH,
                             right_drawer_chamfer_origin[2] + DRAWER_HEIGHT_Z)

    base = (cq
        .Workplane("XY")
        .box(LENGTH_X, WIDTH_Y, HEIGHT_Z)
        .edges("|Z")
        .fillet(CORNERS_FILLET_RADIUS)
        .edges("|X and <Z")
        .fillet(BOTTOM_FILLET_RADIUS)
        .edges(">Z")
        .fillet(TOP_FILLET_RADIUS)
        .faces(">Z") # Portafilter hole
        .workplane(origin=porta_filter_origin)
        .hole(PORTA_HOLDER_DIAMETER, PORTA_HOLDER_DEPTH_Z)
        .faces(">Z") # Portafilter handle cutout
        .workplane(origin=porta_handle_origin)
        .rect(PORTA_HANDLE_WIDTH_X, porta_handle_length_increased)
        .cutBlind(-PORTA_HANDLE_DEPTH_Z)
        .edges(BoxSelector(porta_handle_bbox[0], porta_handle_bbox[1]))
		.fillet(TOP_FILLET_RADIUS)
        .edges(BoxSelector(porta_filter_bbox[0], porta_filter_bbox[1]))
        .fillet(CUTOUT_FILLET_RADIUS)
        .faces(">Z[-2]") # Portafilter handle screw hole
        .workplane(origin=(0.0, -WIDTH_Y / 2.0 + PORTA_HANDLE_LENGTH_Y / 2.0, 0.0))
        .hole(PORTA_HANDLE_SCREW_DIAMETER, PORTA_HANDLE_SCREW_DEPTH_Z)
        .faces(">Z") # Upper left hole
        .workplane(origin=upper_left_origin)
        .hole(UPPER_LEFT_DIAMETER, UPPER_LEFT_DEPTH_Z)
        .edges(BoxSelector(upper_left_bbox[0], upper_left_bbox[1]))
        .fillet(CUTOUT_FILLET_RADIUS)
        .faces(">Z") # Upper middle cutout
        .workplane(origin=upper_middle_origin)
        .rect(UPPER_MIDDLE_LENGTH_X, UPPER_MIDDLE_WIDTH_Y)
        .cutBlind(-UPPER_MIDDLE_DEPTH_Z)
        .edges(BoxSelector(upper_middle_bbox[0], upper_middle_bbox[1]))
        .fillet(CUTOUT_FILLET_RADIUS)
        .faces(">Z") # Upper right hole
        .workplane(origin=upper_right_origin)
        .hole(UPPER_RIGHT_DIAMETER, UPPER_RIGHT_DEPTH_Z)
        .edges(BoxSelector(upper_right_bbox[0], upper_right_bbox[1]))
		.fillet(CUTOUT_FILLET_RADIUS)
        .faces(">Z") # Lower left cuts
        .workplane(origin=lower_left_slots_origin)
        .pushPoints(lower_left_slots_points)
        .rect(LOWER_LEFT_SLOT_WIDTH_X, LOWER_LEFT_SLOT_LENGTH_Y)
        .cutBlind(-LOWER_LEFT_DEPTH_Z)
        .edges(BoxSelector(lower_left_slots_bbox[0], lower_left_slots_bbox[1]))
		.fillet(CUTOUT_FILLET_RADIUS)
        .faces(">Z") # Lower left hole
        .workplane(origin=lower_left_hole_origin)
        .hole(LOWER_LEFT_HOLE_DIAMETER, LOWER_LEFT_DEPTH_Z)
        .edges(BoxSelector(lower_left_hole_bbox[0], lower_left_hole_bbox[1]))
        .fillet(CUTOUT_FILLET_RADIUS)
        .faces(">Z") # Lower right hole
        .workplane(origin=lower_right_origin)
        .hole(LOWER_RIGHT_DIAMETER, LOWER_RIGHT_DEPTH_Z)
        .edges(BoxSelector(lower_right_bbox[0], lower_right_bbox[1]))
		.fillet(CUTOUT_FILLET_RADIUS)
        .faces("<X") # Left drawer cutout
        .workplane(origin=left_drawer_origin)
        .rect(DRAWER_WIDTH_Y, DRAWER_HEIGHT_Z)
        .cutBlind(-DRAWER_DEPTH_X)
        .faces("<Z[3]")
        .edges("<X")
        .chamfer(DRAWER_CHAMFER_LENGTH)
        .faces(BoxSelector(left_drawer_chamfer_bbox[0], left_drawer_chamfer_bbox[1]).__sub__(StringSyntaxSelector("<X")))
        .edges("|Y")[1]
        .fillet(DRAWER_CHAMFER_FILLET_RADIUS)
        .edges(BoxSelector(left_drawer_bbox[0], left_drawer_bbox[1]))
        .fillet(DRAWER_FILLET_RADIUS)
        .faces(">X") # Right drawer cutout
        .workplane(origin=right_drawer_origin)
        .rect(DRAWER_WIDTH_Y, DRAWER_HEIGHT_Z)
        .cutBlind(-DRAWER_DEPTH_X)
        .faces("<Z[3]")
        .edges(">X")
        .chamfer(DRAWER_CHAMFER_LENGTH)
        .faces(BoxSelector(right_drawer_chamfer_bbox[0], right_drawer_chamfer_bbox[1]).__sub__(StringSyntaxSelector(">X")))
        .edges("|Y")[1]
        .fillet(DRAWER_CHAMFER_FILLET_RADIUS)
        .edges(BoxSelector(right_drawer_bbox[0], right_drawer_bbox[1]))
        .fillet(DRAWER_FILLET_RADIUS)
    )

    #objects = base.faces(">Z")
    #selected_objects = cq.Workplane("XY").newObject(objects)
    #cq_utils.show_models(selected_objects=selected_objects)
    #cq_utils.show_models(bounding_box=create_box(right_drawer_bbox))

    all_models = { "tampering station": base }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **all_models)

    # Show in OCP Viewer
    cq_utils.show_models(**all_models)
