def __call__(self, logits: tf.Tensor, labels: tf.Tensor) -> tf.Tensor:
    """Computes and returns a loss based on 1 - dice score.

    Args:
      logits: A Tensor of the prediction.
      labels: A Tensor of the groundtruth label.

    Returns:
      The loss value of (1 - dice score).
    """
    labels = tf.cast(labels, logits.dtype)

    if labels.get_shape().ndims < 2 or logits.get_shape().ndims < 2:
      raise ValueError('The labels and logits must be at least rank 2.')

    epsilon = tf_keras.backend.epsilon()
    keep_label_axis = list(range(len(logits.shape) - 1))
    keep_batch_axis = list(range(1, len(logits.shape)))

    # Compute sample mask to filter out samples with both all-0's labels and
    # predictions because such samples should not contribute to mean dice score
    # in this batch.
    sample_mask = tf.logical_or(
        tf.cast(tf.reduce_sum(labels, axis=keep_batch_axis), dtype=tf.bool),
        tf.cast(tf.reduce_sum(logits, axis=keep_batch_axis), dtype=tf.bool))
    labels = tf.boolean_mask(labels, sample_mask)
    logits = tf.boolean_mask(logits, sample_mask)

    # If all samples are filtered out, return 0 as the loss so this batch does
    # not contribute.
    if labels.shape[0] == 0:
      return tf.convert_to_tensor(0.0)

    # Calculate intersections and unions per class.
    intersection = tf.reduce_sum(labels * logits, axis=keep_label_axis)
    union = tf.reduce_sum(labels + logits, axis=keep_label_axis)

    if self._metric_type == 'generalized':
      # Calculate the volume of groundtruth labels.
      w = tf.math.reciprocal(
          tf.square(tf.reduce_sum(labels, axis=keep_label_axis)) + epsilon)

      # Calculate the weighted dice score and normalizer.
      dice = 2 * tf.reduce_sum(w * intersection)
      normalizer = tf.reduce_sum(w * union)
      if normalizer == 0:
        return tf.convert_to_tensor(1.0)
      dice = tf.cast(dice, dtype=tf.float32)
      normalizer = tf.cast(normalizer, dtype=tf.float32)

      return 1 - tf.reduce_mean(dice / normalizer)
    elif self._metric_type == 'adaptive':
      dice = 2.0 * intersection / (union + epsilon)
      # Calculate weights based on Dice scores.
      weights = tf.exp(-1.0 * dice)

      # Multiply weights by corresponding scores and get sum.
      weighted_dice = tf.reduce_sum(weights * dice)

      # Calculate normalization factor.
      normalizer = tf.cast(tf.size(input=dice), dtype=tf.float32) * tf.exp(-1.0)
      if normalizer == 0:
        return tf.convert_to_tensor(1.0)
      weighted_dice = tf.cast(weighted_dice, dtype=tf.float32)
      return 1 - tf.reduce_mean(weighted_dice / normalizer)
    else:
      summation = tf.reduce_sum(
          labels, axis=self._axis) + tf.reduce_sum(
              logits, axis=self._axis)
      dice = (2 * tf.reduce_sum(labels * logits, axis=self._axis)) / (
          summation + epsilon)
      return 1 - tf.reduce_mean(dice)