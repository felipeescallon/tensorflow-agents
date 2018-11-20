# coding=utf-8
# Copyright 2018 The TF-Agents Authors.
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

"""Sample Keras Value Network.

Implements a network that will generate the following layers:

  [optional]: Conv2D # conv_layer_params
  Flatten
  [optional]: Dense  # fc_layer_params
  Dense -> 1         # Value output
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from tensorflow.keras import layers as keras_layers

from tf_agents.networks import network
from tf_agents.networks import utils
from tf_agents.utils import nest_utils

import gin.tf

nest = tf.contrib.framework.nest


@gin.configurable
class ValueNetwork(network.Network):
  """Feed Forward value network. Reduces to 1 value output per batch item."""

  def __init__(self,
               observation_spec,
               fc_layer_params=(75, 40),
               conv_layer_params=None,
               activation_fn=tf.keras.activations.relu,
               name='ValueNetwork'):
    """Creates an instance of `ValueNetwork`.

    Network supports calls with shape outer_rank + observation_spec.shape. Note
    outer_rank must be at least 1.

    Args:
      observation_spec: A nest of `tensor_spec.TensorSpec` representing the
        observations.
      fc_layer_params: Optional list of fully_connected parameters, where each
        item is the number of units in the layer.
      conv_layer_params: Optional list of convolution layers parameters, where
        each item is a length-three tuple indicating (filters, kernel_size,
        stride).
      activation_fn: Activation function, e.g. tf.keras.activations.relu,.
      name: A string representing name of the network.

    Raises:
      ValueError: If `observation_spec` contains more than one observation.
    """
    super(ValueNetwork, self).__init__(
        observation_spec=observation_spec,
        action_spec=None,
        state_spec=(),
        name=name)

    if len(nest.flatten(observation_spec)) > 1:
      raise ValueError(
          'Network only supports observation_specs with a single observation.')

    self._layers = utils.mlp_layers(
        conv_layer_params,
        fc_layer_params,
        activation_fn=activation_fn,
        kernel_initializer=tf.keras.initializers.glorot_uniform(),
        name='input_mlp')

    self._layers.append(
        keras_layers.Dense(
            1,
            activation=None,
            kernel_initializer=tf.random_uniform_initializer(
                minval=-0.03, maxval=0.03),
        ))

  def call(self, observation, step_type=None, network_state=()):
    del step_type  # unused.

    outer_rank = nest_utils.get_outer_rank(observation, self.observation_spec)
    batch_squash = utils.BatchSquash(outer_rank)

    states = tf.to_float(nest.flatten(observation)[0])
    states = batch_squash.flatten(states)
    for layer in self.layers:
      states = layer(states)

    value = tf.reshape(states, [-1])
    value = batch_squash.unflatten(value)
    return value, network_state
