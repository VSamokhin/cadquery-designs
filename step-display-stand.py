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

import cq_utils
import honeycomb
import cadquery as cq
from cadquery import Workplane


# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False

# Configuration (tweak if needed)
NUM_STEPS = 5
FIRST_STEP_HEIGHT = 15.0
STEP_HEIGHT = 75.0
STEP_WIDTH = 150.0
STEP_DEPTH = 90.0
WALL_THICKNESS = 5.0    # thickness of all walls
CELL_SIZE = 25.0        # hex side length
EDGE_WIDTH = 8.0        # thickness of honeycomb walls (in XY)
SHELL_THICKNESS = EDGE_WIDTH  # thickness of preserved outer shell (in XY)

def generate_step(
        step_height, step_width,
        step_depth, wall_thickness,
        wall_height=0.0) -> tuple[Workplane, Workplane]:
    """
    Generate a single step with given height and width
    """
    half_height = step_height / 2.0
    half_depth = step_depth / 2.0
    x0, y0 = half_depth, -half_height
    x1 = half_depth - wall_thickness
    y2 = half_height - wall_thickness
    x3 = -half_depth - wall_thickness
    y4 = half_height
    step_points = [
        (x0, y0),
        (x1, y0),
        (x1, y2),
        (x3, y2),
        (x3, y4),
        (x0, y4)
    ]
    right_side_points = [
        (x1, y0 - wall_height),
        (x3, y0 - wall_height),
        (x3, y2),
        (x1, y2)
    ]
    origin = (-step_width / 2.0, step_width / 2.0, -step_height / 2.0)
    step = (cq
            .Workplane("YZ", origin=origin)
            .polyline(step_points)
            .close()
            .extrude(step_width))
    right_side = (cq
            .Workplane("YZ", origin=origin)
            .polyline(right_side_points)
            .close()
            .extrude(wall_thickness))
    return step, right_side

def generate_base(right_side: Workplane, step_width, wall_thickness) -> Workplane:
    left_side = cq.Workplane("YZ").copyWorkplane(right_side).translate((step_width - wall_thickness, 0, 0))
    right_side = honeycomb.apply_honeycomb(right_side, CELL_SIZE, EDGE_WIDTH, SHELL_THICKNESS)
    left_side = honeycomb.apply_honeycomb(left_side, CELL_SIZE, EDGE_WIDTH, SHELL_THICKNESS)
    return right_side.union(left_side)

def assembly_stand(
        num_steps=NUM_STEPS,
        first_step_height=FIRST_STEP_HEIGHT,
        step_height=STEP_HEIGHT,
        step_width=STEP_WIDTH,
        step_depth=STEP_DEPTH,
        wall_thickness=WALL_THICKNESS) -> tuple[Workplane, Workplane]:
    """
    Generate a simple assembly stand with multiple steps
    """
    z_offset = -(num_steps - 1) * step_height / 2.0
    y_offset = num_steps * step_depth / 2.0
    all_steps = cq.Workplane("XY")
    right_wall = cq.Workplane("YZ")
    # A bit of overhead for the special first step, but I like the idea
    if first_step_height >= 0.0:
        z_offset -= first_step_height / 2.0
        y_offset -= step_depth / 2.0
        step, _ = generate_step(first_step_height, step_width, step_depth, wall_thickness)
        all_steps = all_steps.union(step.translate((0, y_offset, z_offset)))
        num_steps -= 1

    first_step_offset = first_step_height if first_step_height >= 0.0 else 0.0
    for i in range(num_steps):
        z_offset += step_height
        y_offset -= step_depth
        wall_height = step_height * i + first_step_offset
        step, right_side = generate_step(step_height, step_width, step_depth, wall_thickness, wall_height=wall_height)
        all_steps = all_steps.union(step.translate((0, y_offset, z_offset)))
        right_wall = right_wall.union(right_side.translate((0, y_offset, z_offset)))

    return all_steps, generate_base(right_wall, step_width, wall_thickness)

if __name__ == "__main__":
    steps, base = assembly_stand()

    # Apply honeycomb infill
    #normal_axis = cq_utils.determine_normal_axis(wall)
    #honeycomb_wall = honeycomb.apply_honeycomb(wall, CELL_SIZE, EDGE_WIDTH, SHELL_THICKNESS, normal_axis=normal_axis)

    all_models = { "steps": steps, "base": base }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **all_models)

    # Show in OCP Viewer
    cq_utils.show_models(**all_models)