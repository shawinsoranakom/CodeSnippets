def call(self, inputs):
    if isinstance(inputs, (list, tuple)) and len(inputs) == 2:
      input_tensor, attention_mask = inputs
    else:
      input_tensor, attention_mask = (inputs, None)

    if self._output_range:
      target_tensor = input_tensor[:, 0:self._output_range, :]
      attention_mask = attention_mask[:, 0:self._output_range, :]
    else:
      if self._norm_first:
        source_tensor = input_tensor
        input_tensor = self._attention_layer_norm(input_tensor)
      target_tensor = input_tensor

    attention_output = self._attention_layer(
        query=target_tensor, value=input_tensor, attention_mask=attention_mask)
    attention_output = self._attention_dropout(attention_output)
    if self._norm_first:
      attention_output = source_tensor + attention_output
    else:
      attention_output = self._attention_layer_norm(target_tensor +
                                                    attention_output)
    if self._norm_first:
      source_attention_output = attention_output
      attention_output = self._output_layer_norm(attention_output)

    layer_output = self._output_dense(attention_output)
    layer_output = self._output_dropout(layer_output)
    # During mixed precision training, attention_output is from layer norm and
    # is always fp32 for now. Cast layer_output to fp32 for the subsequent
    # add.
    layer_output = tf.cast(layer_output, tf.float32)
    if self._norm_first:
      layer_output = source_attention_output + layer_output
    else:
      layer_output = self._output_layer_norm(layer_output + attention_output)

    return layer_output