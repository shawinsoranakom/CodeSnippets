def call(self,
           inputs: Tuple[tf.Tensor, tf.Tensor],
           training: Optional[bool] = None) -> tf.Tensor:
    """Calls this decoder sum-merge block with the given input.

    Args:
      inputs: A Tuple of tensors consisting of a low-resolution higher-semantic
        level feature map from the encoder as the first item and a higher
        resolution lower-level feature map from the backbone as the second item.
      training: a `bool` indicating whether it is in `training` mode.
    Note: the first item of the input Tuple takes a lower-resolution feature map
    and the second item of the input Tuple takes a higher-resolution branch.

    Returns:
      A tensor representing the sum-merged decoder feature map.
    """
    if training is None:
      training = tf_keras.backend.learning_phase()
    x_low_res = inputs[0]
    x_high_res = inputs[1]
    if self._low_res_branch:
      for layer in self._low_res_branch:
        x_low_res = layer(x_low_res, training=training)
      x_low_res = self._activation_fn(x_low_res)
    if self._high_res_branch:
      for layer in self._high_res_branch:
        x_high_res = layer(x_high_res, training=training)
      x_high_res = self._activation_fn(x_high_res)
    if self._upsample_low_res is not None:
      x_low_res = self._upsample_low_res(x_low_res)
    if self._upsample_high_res is not None:
      x_high_res = self._upsample_high_res(x_high_res)
    output = self._add_layer([x_low_res, x_high_res])
    return output