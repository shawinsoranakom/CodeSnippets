def call(self, inputs):
    """Transformer self-attention encoder block call.

    Args:
      inputs: a single tensor or a list of tensors. `input tensor` as the single
        sequence of embeddings. [`input tensor`, `attention mask`] to have the
        additional attention mask. [`query tensor`, `key value tensor`,
        `attention mask`] to have separate input streams for the query, and
        key/value to the multi-head attention.

    Returns:
      An output tensor with the same dimensions as input/query tensor.
    """
    if isinstance(inputs, (list, tuple)):
      if len(inputs) == 4:
        (
            input_tensor,
            attention_mask,
            is_index_masked,
            is_index_global_attn,
        ) = inputs
        key_value = None
      elif len(inputs) == 5:
        assert False  # No key_value
      else:
        raise ValueError(
            f"Unexpected inputs to {self.__class__} with length at {len(inputs)}"
        )
    else:
      input_tensor = inputs
      attention_mask = None
      is_index_masked = None
      is_index_global_attn = None
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
      if is_index_masked is not None:
        is_index_masked = is_index_masked[:, 0:self._output_range]
      if is_index_global_attn is not None:
        is_index_global_attn = is_index_global_attn[:, 0:self._output_range]
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
        hidden_states=target_tensor,
        attention_mask=attention_mask,
        is_index_masked=is_index_masked,
        is_index_global_attn=is_index_global_attn,
    )
    # TFLongformerAttention.TFLongformerSelfOutput.* - {.dense}
    attention_output = self._attention_dropout(attention_output)
    if self._norm_first:
      attention_output = source_tensor + attention_output
    else:
      attention_output = self._attention_layer_norm(target_tensor +
                                                    attention_output)
    if self._norm_first:
      source_attention_output = attention_output
      attention_output = self._output_layer_norm(attention_output)
    # TFLongformerIntermediate
    inner_output = self._intermediate_dense(attention_output)
    inner_output = self._intermediate_activation_layer(inner_output)
    inner_output = self._inner_dropout_layer(inner_output)
    # TFLongformerOutput
    layer_output = self._output_dense(inner_output)
    layer_output = self._output_dropout(layer_output)

    if self._norm_first:
      return source_attention_output + layer_output

    # During mixed precision training, layer norm output is always fp32 for now.
    # Casts fp32 for the subsequent add.
    layer_output = tf.cast(layer_output, tf.float32)
    return self._output_layer_norm(layer_output + attention_output)