def call(self, inputs, stride: tf.Tensor, training=None):
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

    if key_value is None:
      key_value = input_tensor

    if self._norm_first:
      source_tensor = input_tensor[:, ::stride, :]
      input_tensor = self._attention_layer_norm(input_tensor, training=training)
    if attention_mask is not None:
      attention_mask = attention_mask[:, ::stride, :]
    target_tensor = input_tensor[:, ::stride, :]

    attention_output = self._attention_layer(
        query=target_tensor,
        value=key_value,
        attention_mask=attention_mask,
        training=training)
    attention_output = self._attention_dropout(
        attention_output, training=training)

    if self._norm_first:
      attention_output = source_tensor + attention_output
    else:
      attention_output = self._attention_layer_norm(
          target_tensor + attention_output, training=training)
    if self._norm_first:
      source_attention_output = attention_output
      attention_output = self._output_layer_norm(
          attention_output, training=training)

    if self._feedforward_block is None:
      intermediate_output = self._intermediate_dense(attention_output)
      intermediate_output = self._intermediate_activation_layer(
          intermediate_output)
      layer_output = self._output_dense(intermediate_output, training=training)
      layer_output = self._output_dropout(layer_output, training=training)
      layer_output = tf.cast(layer_output, tf.float32)
      if self._norm_first:
        layer_output = source_attention_output + layer_output
      else:
        layer_output = self._output_layer_norm(
            layer_output + attention_output, training=training)
    else:
      if self._norm_first:
        # if norm_first, assume the feedforward block will not apply layer norm
        layer_output = self._feedforward_block(
            attention_output, training=training)
        layer_output += source_attention_output
      else:
        # if not norm_first, assume that the feedforwad does apply layer norm
        layer_output = self._feedforward_block(
            attention_output, training=training)

    return layer_output