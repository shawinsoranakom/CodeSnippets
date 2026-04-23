def call(self, inputs):
    """Transformer self-attention encoder block call.

    Args:
      inputs: a single tensor or a list of tensors. `input tensor` as the single
        sequence of embeddings. [`input tensor`, `attention mask`] to have the
        additional attention mask. [`input tensor`, `attention mask`, `query
        embed`] to have an additional position embedding to add.

    Returns:
      An output tensor with the same dimensions as input/query tensor.
    """
    input_tensor, attention_mask, pos_embed = inputs

    key_value = None

    if self._output_range:
      if self._norm_first:
        source_tensor = input_tensor[:, 0:self._output_range, :]
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm(key_value)
      target_tensor = input_tensor[:, 0:self._output_range, :]
      if attention_mask is not None:
        attention_mask = attention_mask[:, 0:self._output_range, :]
    else:
      if self._norm_first:
        source_tensor = input_tensor
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm(key_value)
      target_tensor = input_tensor

    if key_value is None:
      key_value = input_tensor
    attention_output = self._attention_layer(
        query=target_tensor + pos_embed,
        key=key_value + pos_embed,
        value=key_value,
        attention_mask=attention_mask)
    attention_output = self._attention_dropout(attention_output)
    if self._norm_first:
      attention_output = source_tensor + attention_output
    else:
      attention_output = self._attention_layer_norm(target_tensor +
                                                    attention_output)
    if self._norm_first:
      source_attention_output = attention_output
      attention_output = self._output_layer_norm(attention_output)
    inner_output = self._intermediate_dense(attention_output)
    inner_output = self._intermediate_activation_layer(inner_output)
    inner_output = self._inner_dropout_layer(inner_output)
    layer_output = self._output_dense(inner_output)
    layer_output = self._output_dropout(layer_output)

    if self._norm_first:
      return source_attention_output + layer_output

    # During mixed precision training, layer norm output is always fp32 for now.
    # Casts fp32 for the subsequent add.
    layer_output = tf.cast(layer_output, tf.float32)
    return self._output_layer_norm(layer_output + attention_output)