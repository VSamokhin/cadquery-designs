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
# Sliding drawer wrench bits holder. The drawer itself is a bit tray with
# per-bit cylindrical pockets and a rounded front cut-out for finger grip.

import math
import sys

import cadquery as cq
import cq_utils

# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False

# =========================
# Parameters
# =========================
BIT_SPECS = [
    (22.0, 36.0),
    (18.0, 36.0),
    (22.0, 34.5),
    (20.0, 28.0),
    (18.0, 26.0),
    (17.0, 26.5),
]

# Set to 0 for automatic near-square packing.
LAYOUT_COLUMNS = 3

DRAWER_WALL_THICKNESS = 3.0
DRAWER_BIT_CELL_DEPTH = 10.0
POCKET_DIAMETER_CLEARANCE = 0.6
CELL_GAP = 5.0
DRAWER_FRAME_MARGIN = CELL_GAP
DRAWER_GRIP_RADIUS = 25.0
DRAWER_GRIP_VERTICAL_CENTER_P = 0.62

HOUSING_WALL_THICKNESS = DRAWER_WALL_THICKNESS
HOUSING_CLEARANCE = 0.4

def resolve_columns(bit_count: int, columns: int) -> int:
    """Pick a sensible packing width if the user requests auto layout."""
    if columns and columns > 0:
        return columns
    return max(1, math.ceil(math.sqrt(bit_count)))

def arrange_bit_specs(
    bit_specs: list[tuple[float, float]],
    columns: int,
) -> tuple[int, int, float, float, float, float, float, float, list[tuple[float, float, float]]]:
    """Return layout metadata and per-bit placement info"""

    resolved_columns = resolve_columns(len(bit_specs), columns)
    rows = math.ceil(len(bit_specs) / resolved_columns)

    max_diameter = 0.0
    max_height = 0.0
    shortest_height = sys.float_info.max
    for diameter, height in bit_specs:
        max_diameter = max(diameter, max_diameter)
        max_height = max(height, max_height)
        shortest_height = min(height, shortest_height)

    pitch = max_diameter + CELL_GAP
    footprint_x = (resolved_columns - 1) * pitch + max_diameter
    footprint_y = (rows - 1) * pitch + max_diameter

    drawer_outer_x = footprint_x + 2.0 * (DRAWER_WALL_THICKNESS + DRAWER_FRAME_MARGIN)
    drawer_outer_y = footprint_y + 2.0 * (DRAWER_WALL_THICKNESS + DRAWER_FRAME_MARGIN)
    drawer_outer_z = max_height

    x_origin = -((resolved_columns - 1) * pitch) / 2.0
    y_origin = -((rows - 1) * pitch) / 2.0

    placements = []
    for index, (diameter, height) in enumerate(bit_specs):
        row = index // resolved_columns
        col = index % resolved_columns
        placements.append((
            x_origin + col * pitch,
            y_origin + row * pitch,
            diameter
        ))

    return (
        resolved_columns,
        rows,
        max_diameter,
        max_height,
        shortest_height,
        drawer_outer_x,
        drawer_outer_y,
        drawer_outer_z,
        placements,
    )

def build_drawer(
    bit_specs: list[tuple[float, float]],
    columns: int,
) -> tuple[cq.Workplane, int, int, float, float, float, float, float]:
    """Build the sliding drawer that also acts as the bit tray."""
    (
        resolved_columns,
        rows,
        max_diameter,
        max_height,
        shortest_height,
        drawer_outer_x,
        drawer_outer_y,
        drawer_outer_z,
        placements,
    ) = arrange_bit_specs(bit_specs, columns)

    assert DRAWER_BIT_CELL_DEPTH <= shortest_height - 5.0, (
        "Bit cell depth must be at least 5 mm smaller than the shortest bit"
    )

    drawer = (
        cq
        .Workplane("XY", origin=(-HOUSING_CLEARANCE / 2.0, 0.0, HOUSING_WALL_THICKNESS))
        .box(drawer_outer_x, drawer_outer_y, DRAWER_BIT_CELL_DEPTH + DRAWER_WALL_THICKNESS, centered=(True, True, False))
        )

    for x, y, diameter in placements:
         drawer = (
             drawer
             .faces(">Z")
             .workplane(origin=(x, y))
             .hole(diameter + POCKET_DIAMETER_CLEARANCE, DRAWER_BIT_CELL_DEPTH)
         )

    front = (
        cq
        .Workplane("YZ", origin=(-drawer_outer_x / 2.0 - DRAWER_WALL_THICKNESS - HOUSING_CLEARANCE / 2.0, 0.0, HOUSING_WALL_THICKNESS))
        .box(drawer_outer_y, drawer_outer_z, DRAWER_WALL_THICKNESS, centered=(True, False, False))
        )

    grip_radius = min(DRAWER_GRIP_RADIUS, drawer_outer_z * 0.45)
    grip_center_z = drawer_outer_z + HOUSING_WALL_THICKNESS
    front = (
        front
        .faces("<X")
        .workplane(origin=(-drawer_outer_x / 2.0 + DRAWER_WALL_THICKNESS / 2.0, 0.0, grip_center_z))
        .hole(grip_radius, DRAWER_WALL_THICKNESS)
        .faces(">Z")
        .fillet(0.5)
    )

    return drawer.union(front), resolved_columns, rows, max_diameter, max_height, drawer_outer_x, drawer_outer_y, drawer_outer_z

def build_housing(drawer_outer_x: float, drawer_outer_y: float, drawer_outer_z: float) -> cq.Workplane:
    """Build a box-like sleeve that the drawer slides in."""
    housing_inner_x = drawer_outer_x + HOUSING_CLEARANCE
    housing_inner_y = drawer_outer_y + 2.0 * HOUSING_CLEARANCE
    housing_inner_z = drawer_outer_z + HOUSING_CLEARANCE

    housing_outer_x = housing_inner_x + 2.0 * HOUSING_WALL_THICKNESS
    housing_outer_y = housing_inner_y + 2.0 * HOUSING_WALL_THICKNESS
    housing_outer_z = housing_inner_z + 2.0 * HOUSING_WALL_THICKNESS

    outer = cq.Workplane("XY").box(housing_outer_x, housing_outer_y, housing_outer_z, centered=(True, True, False))
    inner = (
        cq.Workplane("XY")
        .box(housing_inner_x + HOUSING_WALL_THICKNESS, housing_inner_y, housing_inner_z, centered=(True, True, False))
        .translate((-HOUSING_WALL_THICKNESS / 2.0, 0.0, HOUSING_WALL_THICKNESS))
    )

    return outer.cut(inner)

if __name__ == "__main__":
    drawer, resolved_columns, rows, max_diameter, max_height, drawer_outer_x, drawer_outer_y, drawer_outer_z = build_drawer(
        BIT_SPECS,
        LAYOUT_COLUMNS,
    )
    housing = build_housing(drawer_outer_x, drawer_outer_y, drawer_outer_z)

    drawer_open_distance = drawer_outer_x * 0.35

    model_name = (
        f"wrench-bits-holder-drawer-bits_{len(BIT_SPECS)}-cols_{resolved_columns}"
        f"-max_d_{max_diameter}-max_h_{max_height}-basement_{DRAWER_BIT_CELL_DEPTH}"
    )

    models = {
        f"{model_name}-housing": housing,
        f"{model_name}-drawer": drawer
    }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **models)

    # Show in OCP Viewer
    cq_utils.show_models(**models)
