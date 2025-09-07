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
#
# v0.0.1

import cadquery as cq
from cadquery import Workplane
from ocp_vscode import show_object
import os

# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = True

# Configuration (tweak if needed)
WIDTH_PREAMP, LENGTH_PREAMP, HEIGHT = 120.0, 150.0, 50.0
WIDTH_PSU, LENGTH_PSU = 100.0, 80.0
BASE_WALL_THICK = 3.0       # generic wall thickness
BASE_BOTTOM_THICK = 3.0     # bottom plate thickness
LID_TOP_THICK = 3.0         # lid top plate thickness
LID_WALL_THICK = BASE_WALL_THICK   # side wall thickness attached to lid
PROTRUSION_DEPTH = LID_WALL_THICK  # ledge depth where lid sits in
PEG_DIAMETER = 5.0
PEG_HEIGHT = 3.0
SCREW_DIAMETER = 3.2
SCREW_CSK_DIAMETER = 6.0
SCREW_CSK_ANGLE = 120
BRASS_CSK_DIAMETER = 6.0
BRASS_CSK_ANGLE = 82
CINCH_DIAMETER = 8.0  # diameter of cinch/RCA holes
POWER_DIAMETER = 12.0 # diameter of power connector hole
GND_DIAMETER = 8.0    # diameter of ground connector hole
POWER_SOCKET_WIDTH = 48.0
POWER_SOCKET_HEIGHT = 29.0
BOSS_DIAMETER = 8.0

# Utility: add vents as rectangular slots on a vertical wall workplane
def add_vertical_wall_vents(wall: Workplane, area_length, area_height, wall_thick, spacing=6.0, slot_w=3.0, slot_h=None) -> Workplane:
    if slot_h is None:
        slot_h = max(4.0, area_height - 4.0)

    n = max(1, int(area_length // spacing))
    actual_spacing = area_length / n
    start = -area_length / 2.0 + actual_spacing / 2.0
    ys = [start + i * actual_spacing for i in range(n)]
    pts = [(y, 0) for y in ys]
    # create slots in the wall (workplane coords map to local face Y,Z)
    return (wall
            .pushPoints(pts)
            .rect(slot_w, slot_h)
            .cutBlind(-wall_thick))

def add_diagonal_wall_vents(wall: Workplane, area_length, area_height, wall_thick, width, base_thick=BASE_BOTTOM_THICK, height=HEIGHT, spacing=6.0, slot_w=3.0, slot_h=None, angle=45.0) -> Workplane:
    """
    Add diagonal vents as rectangular slots on a vertical wall workplane.
    I'm lazy to find a better solution, so for to get proper slots in >X faces (symmetrical to those in <X faces),
    simply change the sign of wall_thick, width, and angle values.
    """
    if slot_h is None:
        slot_h = area_height - 4.0

    n = max(1, int(area_length // spacing))
    actual_spacing = area_length / n
    start = -area_length / 2.0 + actual_spacing / 2.0

    x_offset = width / 2.0 - wall_thick / 2.0
    z_offset = height / 2.0 - area_height / 2.0 + base_thick
    cuts = cq.Workplane("XY")
    for i in range(n):
        y = start + i * actual_spacing
        slot = (cq
                .Workplane("XY")
                .rect(wall_thick * 2.0, slot_w)   # long thin rectangle
                .extrude(slot_h)                  # make into a thin plate
                .rotate((0, 0, 0), (0, 0, 1), angle)
                .translate((x_offset, y, z_offset)))
        cuts = cuts.union(slot)

    # subtract the slots
    return wall.cut(cuts)

# Utility: add bottom mounting holes (for brass bosses) on bottom plate outer face
def add_bottom_mounts(bottom_plate: Workplane, spacing_x, spacing_y, thru_dia=SCREW_DIAMETER, csk_dia=BRASS_CSK_DIAMETER, csk_angle=BRASS_CSK_ANGLE) -> Workplane:
    hx = spacing_x / 2.0
    hy = spacing_y / 2.0
    pts = [(hx, hy), (-hx, hy), (hx, -hy), (-hx, -hy)]
    return (bottom_plate
            .faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .pushPoints(pts)
            .cskHole(diameter=thru_dia, cskDiameter=csk_dia, cskAngle=csk_angle))

# Utility: add internal bosses in base corners for lid screws
def add_internal_bosses(base: Workplane, lid: Workplane,
                        width, length,
                        height=HEIGHT,
                        boss_dia=BOSS_DIAMETER,
                        hole_dia=SCREW_DIAMETER,
                        inset_x=LID_WALL_THICK,
                        inset_y=BASE_WALL_THICK,
                        bottom_thick=BASE_BOTTOM_THICK,
                        csk_dia=SCREW_CSK_DIAMETER,
                        csk_angle=SCREW_CSK_ANGLE) -> tuple[Workplane, Workplane]:
    # base is the assembled base solid (bottom + walls). We'll place bosses on top of the bottom plate inside
    hx = width / 2.0 - inset_x - boss_dia / 2.0
    hy = length / 2.0 - inset_y - boss_dia / 2.0 + 1.0
    pts = [(hx, hy), (-hx, hy), (hx, -hy), (-hx, -hy)]
    for (x, y) in pts:
        # create a cylinder rising from inside bottom surface
        boss = (cq
                .Workplane("XY")
                .transformed(offset=(x, y, 0))
                .circle(boss_dia / 2.0)
                .extrude(height - bottom_thick / 2.0)
                .faces(">Z")
                .workplane(centerOption="CenterOfMass")
                .hole(hole_dia, depth=20.0)) # hole for screw into boss (from lid screw down)
        base = base.union(boss)

        lid = (lid
               .faces(">Z")
               .workplane(centerOption="CenterOfMass")
               .pushPoints(pts)
               .cskHole(diameter=hole_dia, cskDiameter=csk_dia, cskAngle=csk_angle))

    return base, lid

# Build base: bottom plate + front and rear walls attached
def build_base(width, length, bottom_thick=BASE_BOTTOM_THICK, wall_thick=BASE_WALL_THICK, wall_height=HEIGHT, top_thick=LID_TOP_THICK) -> Workplane:
    # bottom plate centered at origin, thickness bottom_thick
    bottom = (cq
              .Workplane("XY")
              .box(width, length, bottom_thick, centered=(True, True, False)))

    front_rear_length = width - wall_thick * 2.0
    front_rear_height = wall_height - top_thick / 2.0
    # front wall (positive Y direction): place at y = + (length/2 - wall_thick/2)
    front = (cq
             .Workplane("XY")
             .transformed(offset=(0, length / 2.0 - wall_thick / 2.0, 0))
             .box(front_rear_length, wall_thick, front_rear_height, centered=(True, True, False)))

    # rear wall (negative Y): at y = - (length/2 - wall_thick/2)
    rear = (cq
            .Workplane("XY")
            .transformed(offset=(0, -length / 2.0 + wall_thick / 2.0, 0))
            .box(front_rear_length, wall_thick, front_rear_height, centered=(True, True, False)))

    return bottom.union(front).union(rear)

# Build lid: top plate + side walls attached
def build_lid(width, length, top_thick=LID_TOP_THICK, side_thick=LID_WALL_THICK, wall_height=HEIGHT, bottom_thick=BASE_BOTTOM_THICK) -> Workplane:
    # top plate centered at origin but later positioned at top; we'll create centered and translate when assembling
    top = (cq
           .Workplane("XY")
           .transformed(offset=(0, 0, wall_height-top_thick/2.0))
           .box(width, length, top_thick, centered=(True, True, False)))

    left_right_height = wall_height - bottom_thick
    left_right_z_offset = top_thick
    # left side wall (negative X): create wall and position so it attaches to left edge of top
    left = (cq
            .Workplane("XY")
            .transformed(offset=(-width/2.0 + side_thick/2.0, 0, left_right_z_offset))
            .box(side_thick, length, left_right_height, centered=(True, True, False)))

    # right side wall (positive X)
    right = (cq
             .Workplane("XY")
             .transformed(offset=(width/2.0 - side_thick/2.0, 0, left_right_z_offset))
             .box(side_thick, length, left_right_height, centered=(True, True, False)))

    return top.union(left).union(right)

# Add aligments (protrusions and corresponding ledges) in the bottom plate and the lid walls
def add_aligments(base: Workplane, lid: Workplane, width, bottom_thick=BASE_BOTTOM_THICK, wall_thick=LID_WALL_THICK) -> tuple[Workplane, Workplane]:
    alignment_length = 30.0
    left_x_offset = -width / 2.0 + wall_thick / 2.0
    right_x_offset = width / 2.0 - wall_thick / 2.0
    base = (base
            .faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .moveTo(left_x_offset, 0)
            .rect(wall_thick, alignment_length)
            .cutBlind(until=-bottom_thick) # left protrusion
            .moveTo(right_x_offset, 0)
            .rect(wall_thick, alignment_length)
            .cutBlind(until=-bottom_thick)) # right protrusion

    tolerance = 0.2
    y_offset = -alignment_length / 2.0 + tolerance / 2.0
    # left ledge (negative X)
    left_ledge = (cq
                  .Workplane("XY")
                  .transformed(offset=(left_x_offset, y_offset, 0))
                  .box(wall_thick, alignment_length - tolerance, bottom_thick, centered=(True, False, False)))

    # right ledge (positive X)
    right_ledge = (cq
                  .Workplane("XY")
                  .transformed(offset=(right_x_offset, y_offset, 0))
                  .box(wall_thick, alignment_length - tolerance, bottom_thick, centered=(True, False, False)))

    return base, lid.union(left_ledge).union(right_ledge)

# Create rear wall cutouts (only on rear wall) for preamp
def add_preamp_rear_connectors(base: Workplane, cinch_dia=CINCH_DIAMETER, power_dia=POWER_DIAMETER, ground_dia=GND_DIAMETER, wall_thick=BASE_WALL_THICK) -> Workplane:
    # Place input pair centered at X = -30, power at X = 0, output pair at X = +30 (approx)
    cinch_interval = 15.0
    cinch_offset = 30.0
    return (base
            .faces("<Y")
            .workplane(offset=0, centerOption="CenterOfMass")
            .pushPoints([(-cinch_interval/2.0 - cinch_offset, 0), (cinch_interval/2.0 - cinch_offset, 0)])
            .hole(cinch_dia, depth=wall_thick)  # Input pair
            .pushPoints([(0, -power_dia)])
            .hole(ground_dia, depth=wall_thick)  # Ground terminal
            .pushPoints([(0, 0)])
            .hole(power_dia, depth=wall_thick) # Power in (center)
            .pushPoints([(-cinch_interval/2.0 + cinch_offset, 0), (cinch_interval/2.0 + cinch_offset, 0)])
            .hole(cinch_dia, depth=wall_thick)) # Output pair

# Create rear wall cutouts for PSU
def add_psu_rear_connectors(base: Workplane, width_psu=WIDTH_PSU, power_dia=POWER_DIAMETER, socket_width=POWER_SOCKET_WIDTH, socket_height=POWER_SOCKET_HEIGHT, wall_thick=BASE_WALL_THICK) -> Workplane:
    hole_x_offset = 10.0
    return (base
            .faces("<Y")
            .workplane(centerOption="CenterOfMass")
            .moveTo(-width_psu/2.0 + socket_width/2.0 + hole_x_offset + wall_thick, 0)
            .rect(socket_width, socket_height)
            .cutBlind(until=-wall_thick)  # Power socket cutout
            .pushPoints([(width_psu/2.0 - power_dia/2.0 - hole_x_offset - wall_thick, 0)])
            .hole(power_dia, depth=wall_thick))  # Ground terminal hole below socket

# Export functions
def export_models(preamp_base: Workplane, preamp_lid: Workplane, power_base: Workplane, power_lid: Workplane):
    """Export all models to STL and STEP formats"""

    # Create export directory
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    models = {
        "phono-preamp-base": preamp_base,
        "phono-preamp-lid": preamp_lid,
        "power-supply-base": power_base,
        "power-supply-lid": power_lid
    }

    for name, model in models.items():
        if DO_STL_EXPORT:
            # Export STL
            stl_path = os.path.join(export_dir, f"{name}.stl")
            cq.exporters.export(model, stl_path)
            print(f"Exported {stl_path}")

        if DO_STEP_EXPORT:
            # Export STEP
            step_path = os.path.join(export_dir, f"{name}.step")
            cq.exporters.export(model, step_path)
            print(f"Exported {step_path}")

if __name__ == "__main__":
    # Build and assemble preamp case
    preamp_base = build_base(WIDTH_PREAMP, LENGTH_PREAMP)
    preamp_base = add_bottom_mounts(preamp_base, spacing_x=95.0, spacing_y=115.0)
    preamp_base = add_preamp_rear_connectors(preamp_base)

    # Build preamp lid (top + side walls)
    preamp_lid = build_lid(WIDTH_PREAMP, LENGTH_PREAMP)

    # Add alignments
    preamp_base, preamp_lid = add_aligments(preamp_base, preamp_lid, WIDTH_PREAMP)
    # Add internal bosses for screws
    preamp_base, preamp_lid = add_internal_bosses(preamp_base, preamp_lid, WIDTH_PREAMP, LENGTH_PREAMP)

    print("Preamp case built")

    # Build and assemble PSU case
    psu_base = build_base(WIDTH_PSU, LENGTH_PSU)
    psu_base = add_bottom_mounts(psu_base, spacing_x=65.0, spacing_y=70.0)
    psu_base = add_psu_rear_connectors(psu_base)

    # Build PSU lid (top + side walls)
    psu_lid = build_lid(WIDTH_PSU, LENGTH_PSU)
    # Vents only in the lid side walls
    psu_vent_length = LENGTH_PSU - 20.0
    psu_vent_height = HEIGHT - 10.0
    psu_lid = psu_lid.faces("<X").workplane(centerOption="CenterOfMass")
    #psu_lid = add_vertical_wall_vents(psu_lid, psu_vent_length, psu_vent_height, LID_WALL_THICK)
    psu_lid = add_diagonal_wall_vents(psu_lid, psu_vent_length, psu_vent_height, LID_WALL_THICK, WIDTH_PSU)
    psu_lid = psu_lid.faces(">X").workplane(centerOption="CenterOfMass")
    #psu_lid = add_vertical_wall_vents(psu_lid, psu_vent_length, psu_vent_height, LID_WALL_THICK)
    psu_lid = add_diagonal_wall_vents(psu_lid, psu_vent_length, psu_vent_height, -LID_WALL_THICK, -WIDTH_PSU, angle=-45.0)

    # Add alignments
    psu_base, psu_lid = add_aligments(psu_base, psu_lid, WIDTH_PSU)
    # Add internal bosses for screws
    psu_base, psu_lid = add_internal_bosses(psu_base, psu_lid, WIDTH_PSU, LENGTH_PSU)

    print("PSU case built")

    # Optional export
    export_models(preamp_base, preamp_lid, psu_base, psu_lid)

    # Show in CQ-editor
    show_object(preamp_base, name="Preamp Base")
    show_object(preamp_lid, name="Preamp Lid")
    show_object(psu_base, name="PSU Base")
    show_object(psu_lid, name="PSU Lid")
