- This project is a set of Python scripts intended to model 3D printable objects using CADQUERY-
- Project's language is English
- Initial template for every 3D model:
```python
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
# Here comes a model description

import cq_utils
import cadquery as cq

# Toggle exports (set True when you want STL/STEP files written)
DO_STL_EXPORT = True
DO_STEP_EXPORT = False

# =========================
# Parameters
# =========================
PARAMETER1 = 0.0
PARAMETER2 = 0.0

if __name__ == "__main__":

    model1 = None # Here should come the actual implementation

    models = { f'Model name-parameter1_{PARAMETER1}-parameter2_{PARAMETER2}': model1 }

    # Optional export
    cq_utils.export_models(DO_STL_EXPORT, DO_STEP_EXPORT, **models)

    # Show in OCP Viewer
    cq_utils.show_models(**model)
```
- While adding implementation using the template above:
  - replace the copyright year, creator name/e-mail, model description with actual ones
  - substitute the fake parameters with actual ones
  - composing the model name, add to it only the most important parameters, not all of them if there are many, to distinguish one genarated file from another
- Increase the version in the header only once per a commit and only its patch part
- Don't forget to update README.md keeping there only general description of the model and no source code details
- Defining a function, pass ALL its external paremeters as arguments, to those arguments which are bound to user defined configuration, supply these user defined parameters as default values
