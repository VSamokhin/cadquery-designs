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

import cq_utils
import cadquery as cq
import math


# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False

# =========================
# Parameters
# =========================
BASE_W = 18.0          # X
BASE_D = 18.0          # Y
BASE_H = 20.0          # Z
BASE_CORNER_FILLET = 4.0

CUT_OFF_H = 5.0        # Z

EAR_TH = 5.0           # Thickness of ear in X
EAR_HOLE_D = 6.0       # Hole diameter
EAR_OUTER_R = 7.0      # Total length of ear from apex to the farest point of circle is 3 * R
EAR_OFFSET_X = -5.0
EAR_OFFSET_Y = 5.0

# Small rear latch/tab visible on photos (approximate)
REAR_TAB_W = 7.0
REAR_TAB_D = 3.0
REAR_TAB_H = 4.0
REAR_TAB_OFFSET_X = -4.0
REAR_TAB_FILLET = 0.95

RABBET_W = 2.5
RABBET_OFFSET_X1 = 6.0  # Bottom-left
RABBET_OFFSET_X2 = 2.0  # Top-right

if __name__ == "__main__":
    # =========================
    # Base block
    # =========================
    base_x = BASE_W / 2.0
    base_y = BASE_D / 2.0
    base_diff_x = BASE_W / 9.0
    base_p1 = (-base_x, base_y)
    base_p2 = (base_x + base_diff_x, base_y)
    base_p3 = (base_x, -base_y)
    base_p4 = (-base_x, -base_y)
    part = (
        cq.Workplane("XY")
        .polyline([base_p1, base_p2, base_p3, base_p4])
        .close()
        .extrude(BASE_H)
        .edges("|Z")
        .fillet(BASE_CORNER_FILLET)
    )

    # =========================
    # Ear / lug
    # =========================
    apex = (0.0, 0.0)
    left_base = (-1.5 * EAR_OUTER_R, -math.sqrt(3) * EAR_OUTER_R / 2.0)
    right_base = (-1.5 * EAR_OUTER_R, math.sqrt(3) * EAR_OUTER_R / 2.0)
    circle_center_yz = (-2.0 * EAR_OUTER_R, 0.0)

    ear_profile = (
        cq.Workplane("YZ", origin=(EAR_OFFSET_X, EAR_OFFSET_Y, BASE_H))
        .polyline([left_base, apex, right_base])
        .close()
        .pushPoints([circle_center_yz])
        .circle(EAR_OUTER_R)
        .extrude(EAR_TH)
        #.edges("|X and (>Z or <Z)")
        #.fillet(EAR_OUTER_RADIUS - 1.0)
    )

    # =========================
    # L-shaped cut-off
    # =========================
    cut_off = (
        cq.Workplane("XY", origin=(0.0, 0.0, BASE_H - CUT_OFF_H))
        .polyline([base_p1, (EAR_OFFSET_X, base_p1[1]), (EAR_OFFSET_X, base_p4[1]), base_p4])
        .close()
        .polyline([(EAR_OFFSET_X, base_p1[1]), base_p2, (base_p2[0], EAR_OFFSET_Y), (EAR_OFFSET_X, EAR_OFFSET_Y)])
        .close()
        .extrude(CUT_OFF_H)
    )

    part = part.cut(cut_off)

    # =========================
    # Hole
    # =========================
    part = (
        part.union(ear_profile)
        .faces("<X")
        .workplane()
        .pushPoints([(2.0 * EAR_OUTER_R - EAR_OFFSET_Y, BASE_H)])
        .hole(EAR_HOLE_D)
    )

    # =========================
    # Small R-shaped tab / stop
    # =========================
    tab_p1 = (0.0, REAR_TAB_H)
    tab_p2 = (REAR_TAB_D, REAR_TAB_H)
    tab_p3 = (REAR_TAB_D, REAR_TAB_H / 2.0)
    tab_p4 = (REAR_TAB_D / 2.0, REAR_TAB_H / 2.0)
    tab_p5 = (REAR_TAB_D / 2.0, 0.0)
    tab_p6 = (0.0, 0.0)
    rear_tab = (
        cq.Workplane("YZ", origin=(REAR_TAB_OFFSET_X, EAR_OFFSET_Y, BASE_H - CUT_OFF_H))
        .polyline([tab_p1, tab_p2, tab_p3, tab_p4, tab_p5, tab_p6])
        .close()
        .extrude(REAR_TAB_W)
        .faces(">Y")
        .edges("|X ")
        .fillet(REAR_TAB_FILLET)
    )

    part = part.union(rear_tab)

    # =========================
    # Rabbet
    # =========================
    rabbet_left_x = -BASE_W / 2.0 + RABBET_OFFSET_X1 + RABBET_W / 2.0
    rabbet_right_x = BASE_W / 2.0 - RABBET_OFFSET_X2 - RABBET_W / 2.0
    rabbet_diff_x = rabbet_right_x - rabbet_left_x
    rabbet_center_x = rabbet_left_x + rabbet_diff_x / 2.0
    rabbet_p1 = (rabbet_left_x, 0.0)
    rabbet_p2 = (rabbet_left_x, BASE_H * 0.15)
    rabbet_p3 = (rabbet_center_x, BASE_H * 0.5)
    rabbet_p4 = (rabbet_right_x , BASE_H * 0.85)
    rabbet_p5 = (rabbet_right_x, BASE_H)
    rabbet_offset_z = -BASE_D / 2.0 + RABBET_W / 2.0
    rabbet_path = (
        cq.Workplane("XZ", origin=(0.0, rabbet_offset_z))
        .spline([rabbet_p1, rabbet_p2, rabbet_p3, rabbet_p4, rabbet_p5])
        #.polyline([rabbet_p1, rabbet_p2, rabbet_p3, rabbet_p4, rabbet_p5])
    )

    rabbet = (
        cq.Workplane("XY", origin=(rabbet_p1[0], rabbet_offset_z))
        .rect(RABBET_W, RABBET_W)
        .sweep(rabbet_path, isFrenet=False)
    )

    part = part.cut(rabbet)

    # =========================
    # Final cleanup
    # =========================
    #part = part.faces(">Z").edges().fillet(0.2)

    lug2 = part.mirror()

    model = { "lug 1": part, "lug 2": lug2 }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **model)

    # Show in OCP Viewer
    cq_utils.show_models(**model)
