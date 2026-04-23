def build_call(self, inputs, training=True, intermediates_dict=None):
    """Building the ResNet50 model.

    Args:
      inputs: Images to compute features for.
      training: Whether model is in training phase.
      intermediates_dict: `None` or dictionary. If not None, accumulate feature
        maps from intermediate blocks into the dictionary. ""

    Returns:
      Tensor with featuremap.
    """

    x = self.conv1(inputs)
    x = self.bn_conv1(x, training=training)
    x = tf.nn.relu(x)
    if intermediates_dict is not None:
      intermediates_dict['block0'] = x

    x = self.max_pool(x)
    if intermediates_dict is not None:
      intermediates_dict['block0mp'] = x

    # Block 1 (equivalent to "conv2" in Resnet paper).
    x = self.l2a(x, training=training)
    x = self.l2b(x, training=training)
    x = self.l2c(x, training=training)
    if intermediates_dict is not None:
      intermediates_dict['block1'] = x

    # Block 2 (equivalent to "conv3" in Resnet paper).
    x = self.l3a(x, training=training)
    x = self.l3b(x, training=training)
    x = self.l3c(x, training=training)
    x = self.l3d(x, training=training)
    if intermediates_dict is not None:
      intermediates_dict['block2'] = x

    # Block 3 (equivalent to "conv4" in Resnet paper).
    x = self.l4a(x, training=training)
    x = self.l4b(x, training=training)
    x = self.l4c(x, training=training)
    x = self.l4d(x, training=training)
    x = self.l4e(x, training=training)
    x = self.l4f(x, training=training)

    if self.block3_strides:
      x = self.subsampling_layer(x)
      if intermediates_dict is not None:
        intermediates_dict['block3'] = x
    else:
      if intermediates_dict is not None:
        intermediates_dict['block3'] = x

    x = self.l5a(x, training=training)
    x = self.l5b(x, training=training)
    x = self.l5c(x, training=training)

    if self.average_pooling:
      x = self.avg_pool(x)
      if intermediates_dict is not None:
        intermediates_dict['block4'] = x
    else:
      if intermediates_dict is not None:
        intermediates_dict['block4'] = x

    if self.include_top:
      return self.fc1000(self.flatten(x))
    elif self.global_pooling:
      x = self.global_pooling(x)
      if self.embedding_layer:
        x = self.embedding_layer(x)
      return x
    else:
      return x