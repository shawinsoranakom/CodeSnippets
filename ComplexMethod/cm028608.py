def call(self, inputs, training=None):
    shortcut = inputs
    x = inputs
    if self._start_dw_kernel_size:
      x = self._start_dw_conv(x)
      x = self._start_dw_norm(x)

    x = self._expand_conv(x)
    x = self._expand_norm(x)
    x = self._expand_act(x)

    if self._middle_dw_kernel_size:
      x = self._middle_dw_conv(x)
      x = self._middle_dw_norm(x)
      x = self._middle_dw_act(x)

    x = self._proj_conv(x)
    x = self._proj_norm(x)

    if self._end_dw_kernel_size:
      x = self._end_dw_conv(x)
      x = self._end_dw_norm(x)

    if self._use_layer_scale:
      x = self._layer_scale(x)

    if (
        self._use_residual
        and self._in_filters == self._out_filters
        and self._strides == 1
    ):
      if self._stochastic_depth:
        x = self._stochastic_depth(x, training=training)
      x = x + shortcut

    # Return empty intermediate endpoints to be compatible with other blocks.
    if self._output_intermediate_endpoints:
      return x, {}
    return x