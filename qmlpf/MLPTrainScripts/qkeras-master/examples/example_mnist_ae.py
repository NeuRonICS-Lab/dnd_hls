## This file is part of https://github.com/SensorsINI/dnd_hls. 
## This intellectual property is licensed under the terms of the project license available at the root of the project.
# Copyright 2019 Google LLC
#
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
# ==============================================================================
"""uses po2."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from collections import defaultdict

import tensorflow.keras.backend as K
from tensorflow.keras.datasets import mnist
from tensorflow.keras.layers import Activation
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Input
from tensorflow.keras.layers import *
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.utils import to_categorical

from qkeras import *
from qkeras.utils import model_save_quantized_weights


import numpy as np
import tensorflow.compat.v1 as tf

np.random.seed(42)

NB_EPOCH = 100
BATCH_SIZE = 64
VERBOSE = 1
NB_CLASSES = 10
OPTIMIZER = Adam(lr=0.0001, decay=0.000025)
VALIDATION_SPLIT = 0.1

train = 1

(x_train, y_train), (x_test, y_test) = mnist.load_data()

RESHAPED = 784

x_train = x_train.astype("float32")
x_test = x_test.astype("float32")

x_train = x_train[..., np.newaxis]
x_test = x_test[..., np.newaxis]

x_train /= 256.0
x_test /= 256.0

print(x_train.shape[0], "train samples")
print(x_test.shape[0], "test samples")

print(y_train[0:10])

y_train = to_categorical(y_train, NB_CLASSES)
y_test = to_categorical(y_test, NB_CLASSES)

x = x_in = Input(
    x_train.shape[1:-1] + (1,))
x = QConv2D(
    32,
    kernel_size=(3, 3),
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x = QActivation("quantized_relu(4,0)")(x)
x = QConv2D(
    16,
    kernel_size=(3, 3),
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x = QActivation("quantized_relu(4,0)")(x)
x = QConv2D(
    8,
    kernel_size=(3, 3),
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x = QActivation("quantized_relu(4,0)")(x)
x = QConv2DTranspose(
    8,
    kernel_size=(3, 3),
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x = QActivation("quantized_relu(4,0)")(x)
x = QConv2DTranspose(
    16,
    kernel_size=(3, 3),
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x = QActivation("quantized_relu(4,0)")(x)
x = QConv2DTranspose(
    32,
    kernel_size=(3, 3),
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x = QActivation("quantized_relu(4,0)")(x)
x = QConv2D(
    1,
    kernel_size=(3, 3),
    padding="same",
    kernel_quantizer=quantized_bits(4,0,1),
    bias_quantizer=quantized_bits(4,0,1))(x)
x_out = x
x = Activation("sigmoid")(x)

model = Model(inputs=[x_in], outputs=[x])
mo = Model(inputs=[x_in], outputs=[x_out])
model.summary()

model.compile(
    loss="binary_crossentropy", optimizer=OPTIMIZER, metrics=["accuracy"])

if train:

  history = model.fit(
      x_train, x_train, batch_size=BATCH_SIZE,
      epochs=NB_EPOCH, initial_epoch=1, verbose=VERBOSE,
      validation_split=VALIDATION_SPLIT)

  # Generate reconstructions
  num_reco = 8
  samples = x_test[:num_reco]
  targets = y_test[:num_reco]
  reconstructions = model.predict(samples)


for layer in model.layers:
  for w, weight in enumerate(layer.get_weights()):
    print(layer.name, w, weight.shape)

print_qstats(model)
