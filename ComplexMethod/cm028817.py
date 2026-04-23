def call(self, inputs):
    """Run layer computation."""
    if self._use_cpe:
      x = self._cpe_dw_conv(inputs)
      x = x + inputs
      cpe_outputs = x
    else:
      cpe_outputs = inputs

    shortcut = cpe_outputs
    x = self._input_norm(cpe_outputs)

    if self._use_multi_query:
      if (
          self._query_h_strides > 1
          or self._query_w_strides > 1
          or self._kv_strides > 1
      ):
        x = self._multi_query_attention(x)
      else:
        x = self._multi_query_attention((x, x))
    else:
      x = self._multi_head_attention(x, x)

    if self._use_layer_scale:
      x = self._layer_scale(x)

    if self._use_residual:
      if self._stochastic_depth:
        x = self._stochastic_depth(x)
      x = x + shortcut

    # Return empty intermediate endpoints to be compatible with other blocks.
    if self._output_intermediate_endpoints:
      return x, {}
    return x