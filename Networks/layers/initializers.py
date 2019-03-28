# Copyright 2019 Jianwei Zhang All Right Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# =================================================================================

import math
from tensorflow.python.ops import init_ops
from tensorflow.python.ops import array_ops


class PriorProbability(init_ops.Initializer):
    """ Apply a prior probability to the weights.
    """

    def __init__(self, probability=0.01):
        self.probability = probability

    def get_config(self):
        return {
            "probability": self.probability
        }

    def __call__(self, shape, dtype=None, partition_info=None):
        # set bias to -log((1 - p)/p) for foreground
        result = array_ops.ones(shape, dtype=dtype) * -math.log((1 - self.probability) / self.probability)

        return result