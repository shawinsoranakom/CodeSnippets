def call(self, inputs):
    """Calls the layer with the given inputs."""
    x = inputs

    # bn_op and activation_op are folded into the '2plus1d' conv layer so that
    # we do not explicitly call them here.
    # TODO(lzyuan): clean the conv layers api once the models are re-trained.
    x = self._conv(x)
    if self._batch_norm is not None and self._conv_type != '2plus1d':
      x = self._batch_norm(x)
    if self._activation_layer is not None and self._conv_type != '2plus1d':
      x = self._activation_layer(x)

    if self._conv_temporal is not None:
      x = self._conv_temporal(x)
      if self._batch_norm_temporal is not None and self._conv_type != '2plus1d':
        x = self._batch_norm_temporal(x)
      if self._activation_layer is not None and self._conv_type != '2plus1d':
        x = self._activation_layer(x)

    return x