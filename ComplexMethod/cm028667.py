def call(self,
           inputs: tf.Tensor,
           states: Optional[nn_layers.States] = None
           ) -> Tuple[tf.Tensor, nn_layers.States]:
    """Calls the layer with the given inputs.

    Args:
      inputs: the input tensor.
      states: a dict of states such that, if any of the keys match for this
          layer, will overwrite the contents of the buffer(s).

    Returns:
      the output tensor and states
    """
    states = dict(states) if states is not None else {}

    x = inputs

    # If we have no separate temporal conv, use the buffer before the 3D conv.
    if self._conv_temporal is None and self._stream_buffer is not None:
      x, states = self._stream_buffer(x, states=states)

    # bn_op and activation_op are folded into the '2plus1d' conv layer so that
    # we do not explicitly call them here.
    # TODO(lzyuan): clean the conv layers api once the models are re-trained.
    x = self._conv(x)
    if self._batch_norm is not None and self._conv_type != '2plus1d':
      x = self._batch_norm(x)
    if self._activation_layer is not None and self._conv_type != '2plus1d':
      x = self._activation_layer(x)

    if self._conv_temporal is not None:
      if self._stream_buffer is not None:
        # If we have a separate temporal conv, use the buffer before the
        # 1D conv instead (otherwise, we may waste computation on the 2D conv).
        x, states = self._stream_buffer(x, states=states)

      x = self._conv_temporal(x)
      if self._batch_norm_temporal is not None and self._conv_type != '2plus1d':
        x = self._batch_norm_temporal(x)
      if self._activation_layer is not None and self._conv_type != '2plus1d':
        x = self._activation_layer(x)

    return x, states