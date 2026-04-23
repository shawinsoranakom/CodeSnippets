def call(self, inputs, output_range=None, training=None):
    """Transformer self-attention encoder block call."""
    if isinstance(inputs, (list, tuple)):
      if len(inputs) == 2:
        input_tensor, attention_mask = inputs
        key_value = None
      elif len(inputs) == 3:
        input_tensor, key_value, attention_mask = inputs
      else:
        raise ValueError('Unexpected inputs to %s with length at %d' %
                         (self.__class__, len(inputs)))
    else:
      input_tensor, key_value, attention_mask = (inputs, None, None)

    if output_range is None:
      output_range = self._output_range
    if output_range:
      if self._norm_first:
        source_tensor = input_tensor[:, 0:output_range, :]
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm(key_value)
      target_tensor = input_tensor[:, 0:output_range, :]
      if attention_mask is not None:
        attention_mask = attention_mask[:, 0:output_range, :]
    else:
      if self._norm_first:
        source_tensor = input_tensor
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm(key_value)
      target_tensor = input_tensor

    if key_value is None:
      key_value = input_tensor

    attention_output, attention_scores = self._attention_layer(
        query=target_tensor,
        value=key_value,
        attention_mask=attention_mask,
        return_attention_scores=True)
    attention_output = self._attention_dropout(attention_output)

    attention_output = self._layer_scale_attn(attention_output)

    if self._norm_first:
      # Important to not combine `self._norm_first` and
      # `self._use_query_residual` into one if clause because else is only for
      # `_norm_first == False`.
      if self._use_query_residual:
        attention_output = source_tensor + self._stochastic_depth(
            attention_output, training=training)
      source_attention_output = attention_output
      attention_output = self._output_layer_norm(attention_output)
    else:
      if self._use_query_residual:
        attention_output = target_tensor + self._stochastic_depth(
            attention_output, training=training)
      attention_output = self._attention_layer_norm(attention_output)

    inner_output = self._intermediate_dense(attention_output)
    inner_output = self._intermediate_activation_layer(inner_output)
    inner_output = self._inner_dropout_layer(inner_output)
    layer_output = self._output_dense(inner_output)
    layer_output = self._output_dropout(layer_output)

    # Layerscale after MLP.
    layer_output = self._layer_scale_mlp(layer_output)

    if self._norm_first:
      layer_output = source_attention_output + self._stochastic_depth(
          layer_output, training=training)
    else:
      # During mixed precision training, layer norm output is always fp32 for
      # now. Casts fp32 for the subsequent add.
      layer_output = tf.cast(layer_output, tf.float32)
      layer_output = self._output_layer_norm(
          layer_output
          + self._stochastic_depth(attention_output, training=training))

    if self._return_attention_scores:
      return layer_output, attention_scores
    else:
      return layer_output