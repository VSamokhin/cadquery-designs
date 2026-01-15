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
# v0.0.0
# Home barista's best friend, a tampering station with some additional slots
# to keep tools and accessories like leveler, tamper, screens, porta filters, etc.

import cq_utils
import cadquery as cq


# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False


MARGIN = 10.0

PORTA_HOLDER_DIAMETER = 74.0
PORTA_HOLDER_DEPTH = 75.0
PORTA_HANDLE_LENGTH = 15.0 # Y
PORTA_HANDLE_WIDTH = 25.0 # X
PORTA_HANDLE_DEPTH = 45.0
PORTA_HANDLE_SCREW_DIAMETER = 4.0
PORTA_HANDLE_SCREW_DEPTH = 10.0

UPPER_LEFT_DIAMETER = 60.0
UPPER_LEFT_DEPTH = 15.0

UPPER_MIDDLE_LENGTH = 50.0
UPPER_MIDDLE_WIDTH = 35.0
UPPER_MIDDLE_DEPTH = 35.0

UPPER_RIGHT_DIAMETER = 60.0
UPPER_RIGHT_DEPTH = 15.0

LOWER_LEFT_WIDTH = 3.0 # X
LOWER_LEFT_LENGTH = 50.0 # Y
LOWER_LEFT_DEPTH = 15.0
LOWER_LEFT_GAP = 10.0
LOWER_LEFT_COUNT = 3

LOWER_RIGHT_DIAMETER = 35.0
LOWER_RIGHT_DEPTH = 35.0

INTERNAL_WALL = 5.0

LENGTH = MARGIN + UPPER_LEFT_DIAMETER + PORTA_HOLDER_DIAMETER + UPPER_RIGHT_DIAMETER + MARGIN # X
WIDTH = PORTA_HANDLE_LENGTH + PORTA_HOLDER_DIAMETER + MARGIN + UPPER_MIDDLE_WIDTH + MARGIN # Y
HEIGHT = PORTA_HOLDER_DEPTH + INTERNAL_WALL

DRAWER_WIDTH = 80.0
DRAWER_HEIGHT = HEIGHT - max(UPPER_LEFT_DEPTH, UPPER_RIGHT_DEPTH, LOWER_LEFT_DEPTH, LOWER_RIGHT_DEPTH) - 2 * INTERNAL_WALL
DRAWER_DEPTH = (LENGTH - 2 * INTERNAL_WALL - PORTA_HOLDER_DIAMETER) / 2.0

# Sanity checks
assert (MARGIN + UPPER_LEFT_DIAMETER
        + MARGIN + UPPER_MIDDLE_LENGTH
        + MARGIN + UPPER_RIGHT_DIAMETER + MARGIN < LENGTH), "Wrong upper X dimensions!"
assert (MARGIN + LOWER_LEFT_WIDTH * LOWER_LEFT_COUNT
        + LOWER_LEFT_GAP * (LOWER_LEFT_COUNT - 1)
        + MARGIN + PORTA_HOLDER_DIAMETER
        + MARGIN + LOWER_RIGHT_DIAMETER + MARGIN <= LENGTH), "Wrong lower left X dimensions!"
assert MARGIN + UPPER_LEFT_DIAMETER + MARGIN + LOWER_LEFT_LENGTH + MARGIN <= WIDTH, "Wrong Y dimensions!"

if __name__ == "__main__":

    base = (cq
            .Workplane("XY")
            .box(LENGTH, WIDTH, HEIGHT)
            .edges("|Z")
            .fillet(15.0)
            #.edges("|X and >Z")
            #.fillet(3.0)
            .edges("|X and <Z")
            .fillet(1.5)
            .faces(">Z") # Portafilter handle cutout
            .workplane(origin=(0.0, -WIDTH / 2.0, 0.0))
            .rect(PORTA_HANDLE_WIDTH, PORTA_HOLDER_DIAMETER)
            .cutBlind(-PORTA_HANDLE_DEPTH)
            .faces(">Z[-2]") # Portafilter handle screw hole
            .workplane(origin=(0.0, -WIDTH / 2.0 + PORTA_HANDLE_LENGTH / 2.0, 0.0))
            #.center(0.0, PORTA_HANDLE_LENGTH / 2.0)
            .hole(PORTA_HANDLE_SCREW_DIAMETER, PORTA_HANDLE_SCREW_DEPTH)
            .faces(">Z") # Portafilter hole
            .workplane(origin=(0.0, -WIDTH / 2.0 + PORTA_HANDLE_LENGTH + PORTA_HOLDER_DIAMETER / 2.0, 0.0))
            .hole(PORTA_HOLDER_DIAMETER, PORTA_HOLDER_DEPTH)
            .faces(">Z") # Upper left hole
            .workplane(origin=(-LENGTH / 2.0 + MARGIN + UPPER_LEFT_DIAMETER / 2.0, WIDTH / 2.0 - MARGIN - UPPER_LEFT_DIAMETER / 2.0, 0.0))
            .hole(UPPER_LEFT_DIAMETER, UPPER_LEFT_DEPTH)
            .faces(">Z") # Upper middle cutout
            .workplane(origin=(0.0, WIDTH / 2.0 - MARGIN - UPPER_MIDDLE_WIDTH / 2.0, 0.0))
            .rect(UPPER_MIDDLE_LENGTH, UPPER_MIDDLE_WIDTH)
            .cutBlind(-UPPER_MIDDLE_DEPTH)
            .faces(">Z") # Upper right hole
            .workplane(origin=(LENGTH / 2.0 - MARGIN - UPPER_RIGHT_DIAMETER / 2.0, WIDTH / 2.0 - MARGIN - UPPER_RIGHT_DIAMETER / 2.0, 0.0))
            .hole(UPPER_RIGHT_DIAMETER, UPPER_RIGHT_DEPTH)
            .faces(">Z") # Lower left cuts
            .workplane()
            .pushPoints([((-LENGTH - PORTA_HOLDER_DIAMETER) / 2.0 + (x * LOWER_LEFT_WIDTH + (x - 1) * LOWER_LEFT_GAP) / 2.0, (-WIDTH + MARGIN) / 2.0) for x in range(1, LOWER_LEFT_COUNT + 1)])
            .rect(LOWER_LEFT_WIDTH, LOWER_LEFT_LENGTH)
            .cutBlind(-LOWER_LEFT_DEPTH)
            .faces(">Z") # Lower right hole
            .workplane(origin=(LENGTH / 2.0 - MARGIN - LOWER_RIGHT_DIAMETER / 2.0, -WIDTH / 2.0 + MARGIN + LOWER_RIGHT_DIAMETER / 2.0, 0.0))
            .hole(LOWER_RIGHT_DIAMETER, LOWER_RIGHT_DEPTH)
            .faces("<X") # Left drawer cutout
            .workplane(origin=(0.0, 0.0, -HEIGHT / 2.0 + INTERNAL_WALL + DRAWER_HEIGHT / 2.0))
            .rect(DRAWER_WIDTH, DRAWER_HEIGHT)
            .cutBlind(-DRAWER_DEPTH)
            .faces(">X") # Right drawer cutout
            .workplane(origin=(0.0, 0.0, -HEIGHT / 2.0 + INTERNAL_WALL + DRAWER_HEIGHT / 2.0))
            .rect(DRAWER_WIDTH, DRAWER_HEIGHT)
            .cutBlind(-DRAWER_DEPTH)
    )

    all_models = { "tampering_station": base }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **all_models)

    # Show in OCP Viewer
    cq_utils.show_models(**all_models)