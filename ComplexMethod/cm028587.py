def call(self,
           inputs: Union[tf.Tensor, Dict[str, tf.Tensor]],
           training: Optional[bool] = None) -> tf.Tensor:
    """Calls this MOSAIC encoder block with the given input."""
    if training is None:
      training = tf_keras.backend.learning_phase()
    input_from_backbone_output = (
        inputs[self._encoder_input_level]
        if isinstance(inputs, dict) else inputs)
    branches = []
    # Original features from the final output of the backbone.
    branches.append(input_from_backbone_output)
    if self._spatial_pyramid:
      for bin_pool_level in self._spatial_pyramid:
        x = input_from_backbone_output
        x = bin_pool_level(x)
        x = self._multi_kernel_group_conv(x, training=training)
        x = self._upsample(x)
        branches.append(x)
    if self._global_pool_branch is not None:
      x = input_from_backbone_output
      for layer in self._global_pool_branch:
        x = layer(x, training=training)
      x = self._activation_fn(x)
      x = self._upsample(x)
      branches.append(x)
    x = self._concat_layer(branches)
    for layer in self._encoder_projection:
      x = layer(x, training=training)
    x = self._activation_fn(x)
    if self._encoder_end_dropout_layer is not None:
      x = self._encoder_end_dropout_layer(x, training=training)
    return x