def update_state(self, y_true: tf.Tensor, y_pred: tf.Tensor):
    """Updates metric state.

    Args:
      y_true: The true labels of size [batch, width, height, volume,
        num_classes].
      y_pred: The prediction of size [batch, width, height, volume,
        num_classes].

    Raises:
      ValueError: If number of classes from groundtruth label does not equal to
        `num_classes`.
    """
    if self._num_classes != y_true.get_shape()[-1]:
      raise ValueError(
          'The number of classes from groundtruth labels and `num_classes` '
          'should equal, but they are {0} and {1}.'.format(
              self._num_classes,
              y_true.get_shape()[-1]))

    # If both y_pred and y_true are all 0s, we skip computing the metrics;
    # otherwise the averaged metrics will be erroneously lower.
    if tf.reduce_sum(y_true) != 0 or tf.reduce_sum(y_pred) != 0:
      self._count.assign_add(1.)
      self._dice_scores_overall.assign_add(
          1 - self._dice_op_overall(y_pred, y_true))
      if self._per_class_metric:
        for class_id in range(self._num_classes):
          if tf.reduce_sum(y_true[..., class_id]) != 0 or tf.reduce_sum(
              y_pred[..., class_id]) != 0:
            self._count_per_class[class_id].assign_add(1.)
            self._dice_scores_per_class[class_id].assign_add(
                1 - self._dice_op_per_class(y_pred[...,
                                                   class_id], y_true[...,
                                                                     class_id]))