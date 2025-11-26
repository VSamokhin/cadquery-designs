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
FIRST_STEP_HEIGHT = 15.0           # special first step height (set <0 to disable)
STEP_HEIGHT = 75.0
STEP_WIDTH = 150.0
STEP_DEPTH = 90.0
SIDE_HEIGHT = 0.0                 # height of side walls
WALL_THICKNESS = 3.5               # thickness of all walls
CELL_SIZE = 20.0                   # hex side length
EDGE_WIDTH = WALL_THICKNESS * 2.0  # thickness of honeycomb walls
SHELL_THICKNESS = EDGE_WIDTH       # thickness of preserved outer shell

def generate_step(
        step_height, step_width,
        step_depth, wall_thickness,
        side_height,
        front_z_offset=0.0,
        support_height=0.0) -> tuple[Workplane, Workplane, Workplane]:
    """
    Generate a single step with given height and width
    """
    half_height = step_height / 2.0
    half_depth = step_depth / 2.0
    half_wall_thickness = wall_thickness / 2.0
    x0 = half_depth
    x1 = half_depth - wall_thickness
    x2 = -half_depth
    x3 = -half_depth - wall_thickness
    y0 = -half_height
    y1 = half_height - wall_thickness
    y2 = half_height - half_wall_thickness
    y3 = half_height
    y4 = half_height + side_height
    origin = (-step_width / 2.0, step_width / 2.0, -step_height / 2.0)

    front_points = [
        (x0, y0 - front_z_offset),
        (x1, y0 - front_z_offset),
        (x1, y3),
        (x0, y3)
    ]
    front = (cq
            .Workplane("YZ", origin=origin)
            .polyline(front_points)
            .close()
            .extrude(step_width))

    step_points = [
        (x1, y1),
        (x2, y1),
        (x2, y3),
        (x1, y3)
    ]
    step = (cq
            .Workplane("YZ", origin=origin)
            .polyline(step_points)
            .close()
            .extrude(step_width))

    if side_height > 0.0:
        side_points = [
            (x0, y3),
            (x1, y3),
            (x1, y4),
            (x0, y4)
            ]
        side = (cq
            .Workplane("YZ", origin=origin)
            .polyline(side_points)
            .close()
            .extrude(step_width))
        side = side.edges("|Y and >Z").fillet(wall_thickness)
        step = step.union(side)

    support_points = [
        (x2, y0 - support_height),
        (x3, y0 - support_height),
        (x3, y2),
        (x2, y2)
    ]
    support = (cq
               .Workplane("YZ", origin=origin)
               .polyline(support_points)
               .close()
               .extrude(step_width))

    return front, step, support

def combine_parts(
        front: Workplane, step: Workplane, support: Workplane,
        apply_honeycomb: bool,
        y_offset, z_offset, connector_z_offset,
        cell_size, edge_width, shell_thickness) -> Workplane:
    if apply_honeycomb:
        front = honeycomb.apply_honeycomb(
            front,
            cell_size=cell_size,
            edge_width=edge_width,
            shell_thickness=shell_thickness)
        support = honeycomb.apply_honeycomb(
            support,
            cell_size=cell_size,
            edge_width=edge_width,
            shell_thickness=shell_thickness)

    front = front.translate((0, y_offset, z_offset))
    step = step.translate((0, y_offset, z_offset))
    support = support.translate((0, y_offset, z_offset))
    connector = cq.Workplane("YZ").copyWorkplane(step).translate((0, 0, -connector_z_offset))
    connector = honeycomb.apply_honeycomb(
        connector,
        cell_size=cell_size,
        edge_width=edge_width,
        shell_thickness=shell_thickness)

    return front.union(step).union(support).union(connector)

def assembly_stand(
        num_steps: int=NUM_STEPS,
        first_step_height=FIRST_STEP_HEIGHT,
        step_height=STEP_HEIGHT,
        step_width=STEP_WIDTH,
        step_depth=STEP_DEPTH,
        wall_thickness=WALL_THICKNESS,
        side_height=SIDE_HEIGHT,
        cell_size=CELL_SIZE,
        edge_width=EDGE_WIDTH,
        shell_thickness=SHELL_THICKNESS) -> Workplane:
    """
    Generate a simple assembly stand with multiple steps
    """
    assert num_steps > 0, "Number of steps must greater than zero"
    z_offset = -(num_steps - 1) * step_height / 2.0
    y_offset = num_steps * step_depth / 2.0
    min_wall_size = shell_thickness * 2 + edge_width * 2 + cell_size
    all_steps = cq.Workplane("XY")
    # A bit of overhead for the special first step, but I like the idea of such a step
    if first_step_height >= 0.0:
        assert num_steps > 1, "With the first step enabled, number of steps must be greater than one"
        z_offset -= first_step_height / 2.0
        y_offset -= step_depth / 2.0
        front, step, support = generate_step(
            first_step_height, step_width, step_depth,
            wall_thickness, side_height)
        all_steps = all_steps.union(combine_parts(
            front, step, support,
            apply_honeycomb=first_step_height > min_wall_size,
            y_offset=y_offset, z_offset=z_offset,
            connector_z_offset=0.0,
            cell_size=cell_size, edge_width=edge_width,
            shell_thickness=shell_thickness))
        num_steps -= 1

    first_step_offset = first_step_height if first_step_height >= 0.0 else 0.0
    for i in range(num_steps):
        z_offset += step_height
        y_offset -= step_depth
        support_height = step_height * i + first_step_offset
        front, step, support = generate_step(
            step_height, step_width, step_depth,
            wall_thickness, side_height,
            front_z_offset=wall_thickness/2.0,
            support_height=support_height)
        all_steps = all_steps.union(combine_parts(
            front, step, support,
            apply_honeycomb=step_height > min_wall_size,
            y_offset=y_offset, z_offset=z_offset,
            connector_z_offset=support_height + step_height - wall_thickness * 2.0,
            cell_size=cell_size, edge_width=edge_width,
            shell_thickness=shell_thickness))

    return all_steps

if __name__ == "__main__":
    steps = assembly_stand()

    all_models = { "steps": steps }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **all_models)

    # Show in OCP Viewer
    cq_utils.show_models(**all_models)