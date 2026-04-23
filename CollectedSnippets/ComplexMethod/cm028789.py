def __call__(self, logits, labels, **kwargs):
    """Computes `SegmentationLoss`.

    Args:
      logits: A float tensor in shape (batch_size, height, width, num_classes)
        which is the output of the network.
      labels: A tensor in shape (batch_size, height, width, num_layers), which
        is the label masks of the ground truth. The num_layers can be > 1 if the
        pixels are labeled as multiple classes.
      **kwargs: additional keyword arguments.

    Returns:
       A 0-D float which stores the overall loss of the batch.
    """
    _, height, width, num_classes = logits.get_shape().as_list()
    output_dtype = logits.dtype
    num_layers = labels.get_shape().as_list()[-1]
    if not self._use_binary_cross_entropy:
      if num_layers > 1:
        raise ValueError(
            'Groundtruth mask must have only 1 layer if using categorical'
            'cross entropy, but got {} layers.'.format(num_layers))
    if self._gt_is_matting_map:
      if num_classes != 2:
        raise ValueError(
            'Groundtruth matting map only supports 2 classes, but got {} '
            'classes.'.format(num_classes))
      if num_layers > 1:
        raise ValueError(
            'Groundtruth matting map must have only 1 layer, but got {} '
            'layers.'.format(num_layers))

    class_weights = (
        self._class_weights if self._class_weights else [1] * num_classes)
    if num_classes != len(class_weights):
      raise ValueError(
          'Length of class_weights should be {}'.format(num_classes))
    class_weights = tf.constant(class_weights, dtype=output_dtype)

    if not self._gt_is_matting_map:
      labels = tf.cast(labels, tf.int32)
    if self._use_groundtruth_dimension:
      # TODO(arashwan): Test using align corners to match deeplab alignment.
      logits = tf.image.resize(
          logits, tf.shape(labels)[1:3], method=tf.image.ResizeMethod.BILINEAR)
    else:
      labels = tf.image.resize(
          labels, (height, width),
          method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

    valid_mask = tf.not_equal(tf.cast(labels, tf.int32), self._ignore_label)

    # (batch_size, height, width, num_classes)
    labels_with_prob = self.get_labels_with_prob(logits, labels, valid_mask,
                                                 **kwargs)

    # (batch_size, height, width)
    valid_mask = tf.cast(tf.reduce_any(valid_mask, axis=-1), dtype=output_dtype)

    if self._use_binary_cross_entropy:
      # (batch_size, height, width, num_classes)
      cross_entropy_loss = tf.nn.sigmoid_cross_entropy_with_logits(
          labels=labels_with_prob, logits=logits)
      # (batch_size, height, width, num_classes)
      cross_entropy_loss *= class_weights
      num_valid_values = tf.reduce_sum(valid_mask) * tf.cast(
          num_classes, output_dtype)
      # (batch_size, height, width, num_classes)
      cross_entropy_loss *= valid_mask[..., tf.newaxis]
    else:
      # (batch_size, height, width)
      cross_entropy_loss = tf.nn.softmax_cross_entropy_with_logits(
          labels=labels_with_prob, logits=logits)

      # If groundtruth is matting map, binarize the value to create the weight
      # mask
      if self._gt_is_matting_map:
        labels = utils.binarize_matting_map(labels)

      # (batch_size, height, width)
      weight_mask = tf.einsum(
          '...y,y->...',
          tf.one_hot(
              tf.cast(tf.squeeze(labels, axis=-1), tf.int32),
              depth=num_classes,
              dtype=output_dtype), class_weights)
      cross_entropy_loss *= weight_mask
      num_valid_values = tf.reduce_sum(valid_mask)
      cross_entropy_loss *= valid_mask

    if self._top_k_percent_pixels < 1.0:
      return self.aggregate_loss_top_k(cross_entropy_loss, num_valid_values)
    else:
      return tf.reduce_sum(cross_entropy_loss) / (num_valid_values + EPSILON)