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
# Two hollow cone columns, one with a built-in ISO-thread and the other with a recess for a separate nut.
# I use these as limiters on my roller shutters.

import cq_utils
import cadquery as cq
from cq_warehouse.thread import IsoThread


# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False

# Configuration (tweak if needed)
BASE_DIAMETER = 23.0
TOP_DIAMETER = 19.0
HEIGHT = 40.0

HOLE_DIAMETER = 15.0

# Cone with embedded thread
# E.g. M5: 5.0/0.8, M6: 6.0/1.0
THREAD_DIAMETER = 6.0
THREAD_PITCH = 1.0
THREAD_LENGTH = 6.0

# Cone with recess for a nut
NUT_DIAMETER = 9.5
NUT_HEIGHT = 4.5
BOTTOM_THICK = 4.0
SCREW_HOLE_DIAMETER = 6.0

if __name__ == "__main__":
    thread = IsoThread(
        major_diameter=THREAD_DIAMETER,
        pitch=THREAD_PITCH,
        length=THREAD_LENGTH,
        external=False,
        end_finishes=("fade", "square") # "chamfer" doesn't work with arbitrary lengths
    )

    cone = (cq
            .Solid
            .makeCone(BASE_DIAMETER / 2.0, TOP_DIAMETER / 2.0, HEIGHT))

    column_with_thread = (cq
                          .Workplane("XY")
                          .add(cone)
                          .faces(">Z")
                          .hole(HOLE_DIAMETER, HEIGHT - THREAD_LENGTH)
                          .faces("<Z")
                          .workplane()
                          .hole(THREAD_DIAMETER, depth=THREAD_LENGTH)
                          .union(thread)
                          )

    nut = (cq
           .Workplane("XY", origin=(0, 0, BOTTOM_THICK))
           .polygon(6, NUT_DIAMETER)
           .extrude(NUT_HEIGHT))

    column_for_nut = (cq
                      .Workplane("XY")
                      .add(cone)
                      .faces(">Z")
                      .hole(HOLE_DIAMETER, HEIGHT - NUT_HEIGHT - BOTTOM_THICK)
                      .cut(nut)
                      .faces("<Z")
                      .workplane()
                      .hole(SCREW_HOLE_DIAMETER, depth=BOTTOM_THICK))

    all_models = { "column_with_thread": column_with_thread, "column_for_nut": column_for_nut }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **all_models)

    # Show in OCP Viewer
    cq_utils.show_models(**all_models)