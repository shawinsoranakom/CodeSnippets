def call(self, inputs, training=None):
    endpoints = {}
    shortcut = inputs
    if self._expand_ratio > 1:
      x = self._conv0(inputs)
      x = self._norm0(x)
      x = self._activation_layer(x)
    else:
      x = inputs

    if self._use_depthwise:
      x = self._conv1(x)
      x = self._norm1(x)
      x = self._depthwise_activation_layer(x)
      if self._output_intermediate_endpoints:
        endpoints['depthwise'] = x

    if self._squeeze_excitation:
      x = self._squeeze_excitation(x)

    x = self._conv2(x)
    x = self._norm2(x)

    if (self._use_residual and self._in_filters == self._out_filters and
        self._strides == 1):
      if self._stochastic_depth:
        x = self._stochastic_depth(x, training=training)
      x = self._add([x, shortcut])

    if self._output_intermediate_endpoints:
      return x, endpoints
    return x