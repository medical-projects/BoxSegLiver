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

import tensorflow as tf
import tensorflow.contrib.slim as slim

import loss_metrics as losses
from Networks import base

ModeKeys = tf.estimator.ModeKeys
metrics = losses


class UNet(base.BaseNet):
    def __init__(self, args, name=None):
        super(UNet, self).__init__(args)
        self.name = name
        self.classes.extend(self.args.classes)

    def _net_arg_scope(self, *args, **kwargs):
        normalizer, params = self._get_normalization()
        with slim.arg_scope([slim.conv2d],
                            normalizer_fn=normalizer,
                            normalizer_params=params) as scope:
            return scope

    def _build_network(self, *args, **kwargs):
        out_channels = kwargs.get("init_channels", 64)
        num_down_samples = kwargs.get("num_down_samples", 4)

        tensor_out = self._inputs["images"]
        with tf.variable_scope(self.name, "UNet"):
            encoder_layers = {}

            # encoder
            for i in range(num_down_samples):
                with tf.variable_scope("Encode{:d}".format(i + 1)):
                    tensor_out = slim.repeat(tensor_out, 2, slim.conv2d, out_channels, 3)   # Conv-BN-ReLU
                    encoder_layers["Encode{:d}".format(i + 1)] = tensor_out
                    tensor_out = slim.max_pool2d(tensor_out, [2, 2])
                out_channels *= 2

            # Encode-Decode-Bridge
            tensor_out = slim.repeat(tensor_out, 2, slim.conv2d, out_channels, 3, scope="ED-Bridge")

            # decoder
            for i in reversed(range(num_down_samples)):
                out_channels /= 2
                with tf.variable_scope("Decode{:d}".format(i + 1)):
                    tensor_out = slim.conv2d_transpose(tensor_out,
                                                       tensor_out.get_shape()[-1] // 2, 2, 2)
                    tensor_out = tf.concat((encoder_layers["Encode{:d}".format(i + 1)], tensor_out), axis=-1)
                    tensor_out = slim.repeat(tensor_out, 2, slim.conv2d, out_channels, 3)

            # final
            with slim.arg_scope([slim.conv2d],
                                activation_fn=None,
                                normalizer_fn=None, normalizer_params=None):
                logits = slim.conv2d(tensor_out, self.num_classes, 1, scope="AdjustChannels")
                self._layers["logits"] = logits

            # Probability & Prediction
            ret_prob = kwargs.get("ret_prob", False)
            ret_pred = kwargs.get("ret_pred", False)
            if ret_prob or ret_pred:
                probability = slim.softmax(logits)
                split = tf.split(probability, self.num_classes, axis=-1)
                if ret_prob:
                    for i in range(1, self.num_classes):
                        self._layers[self.classes[i] + "Prob"] = split[i]
                if ret_pred:
                    zeros = tf.zeros_like(split[0], dtype=tf.int32)
                    ones = tf.ones_like(zeros, dtype=tf.int32)
                    for i in range(1, self.num_classes):
                        obj = self.classes[i] + "Pred"
                        self._layers[obj] = tf.where(split[i] > 0.5, ones, zeros, name=obj)
                        self._image_summaries[obj] = self._layers[obj]
        return

    def _build_loss(self):
        losses.weighted_sparse_softmax_cross_entropy(
            self._layers["logits"], self._inputs["labels"],
            self.args.loss_weight_type, self._get_weights_params(), name="Losses")

        # Set the name of the total loss as "loss" which will be summarized by Estimator
        with tf.name_scope("Losses"):
            return tf.losses.get_total_loss()

    def _build_metrics(self):
        if self.mode in [ModeKeys.TRAIN, ModeKeys.EVAL]:
            with tf.name_scope("LabelProcess"):
                try:
                    one_hot_label = tf.get_default_graph().get_tensor_by_name("LabelProcess/one_hot:0")
                except KeyError:
                    one_hot_label = tf.one_hot(self._inputs["labels"], self.num_classes)
                split_labels = tf.split(one_hot_label, self.num_classes, axis=-1)
            with tf.name_scope("Metrics"):
                for i in range(1, self.num_classes):
                    obj = self.classes[i]
                    logits = self._layers[obj + "Pred"]
                    labels = split_labels[i]
                    for met in self.args.metrics_train:
                        metric_func = eval("metrics.metric_" + met.lower())
                        metric_func(logits, labels, name=obj + met)

    def _build_summaries(self):
        if self.mode == ModeKeys.TRAIN:
            images = self._inputs["images"]
            tf.summary.image("{}/{}".format(self.args.tag, images.op.name), images,
                             max_outputs=1, collections=[self.DEFAULT])

            labels = tf.expand_dims(self._inputs["labels"], axis=-1)
            tf.summary.image("{}/{}".format(self.args.tag, labels.op.name), labels,
                             max_outputs=1, collections=[self.DEFAULT])

            for key, value in self._image_summaries.items():
                tf.summary.image("{}/{}".format(self.args.tag, key), value,
                                 max_outputs=1, collections=[self.DEFAULT])

            for tensor in losses.get_losses():
                tf.summary.scalar("{}/{}".format(self.args.tag, tensor.op.name), tensor,
                                  collections=[self.DEFAULT])

            for tensor in metrics.get_metrics():
                tf.summary.scalar("{}/{}".format(self.args.tag, tensor.op.name), tensor,
                                  collections=[self.DEFAULT])
        return