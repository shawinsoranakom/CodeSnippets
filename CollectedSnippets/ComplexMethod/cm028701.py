def call(self, inputs, output_range: Optional[tf.Tensor] = None) -> tf.Tensor:
    if isinstance(inputs, (list, tuple)):
      if len(inputs) == 2:
        input_tensor, attention_mask = inputs
        key_value = None
      elif len(inputs) == 3:
        input_tensor, key_value, attention_mask = inputs
      else:
        raise ValueError("Unexpected inputs to %s with length at %d" %
                         (self.__class__, len(inputs)))
    else:
      input_tensor, key_value, attention_mask = (inputs, None, None)

    if output_range is None:
      output_range = self._output_range
    if output_range:
      target_tensor = input_tensor[:, 0:output_range, :]
      if attention_mask is not None:
        attention_mask = attention_mask[:, 0:output_range, :]
    else:
      target_tensor = input_tensor

    if key_value is None:
      key_value = input_tensor

    attention_output = self._attention_layer(
        query=target_tensor, value=key_value, attention_mask=attention_mask)
    attention_output = self._attention_dropout(attention_output)
    attention_output = target_tensor + self._rezero_a * attention_output
    if self._use_layer_norm:
      attention_output = self._attention_layer_norm(attention_output)
    else:
      attention_output = tf.cast(attention_output, tf.float32)

    intermediate_output = self._intermediate_dense(attention_output)
    intermediate_output = self._inner_activation_layer(intermediate_output)
    layer_output = self._output_dense(intermediate_output)
    layer_output = self._output_dropout(layer_output)
    # During mixed precision training, attention_output is from layer norm and
    # is always fp32 for now. Cast layer_output to fp32 for the subsequent add.
    layer_output = attention_output + tf.cast(self._rezero_a_ffn * layer_output,
                                              tf.float32)
    if self._use_layer_norm:
      layer_output = self._output_layer_norm(layer_output)

    return layer_output