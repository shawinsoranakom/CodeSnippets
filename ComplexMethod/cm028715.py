def call(self, inputs):
    """Transformer self-attention encoder block call.

    Args:
      inputs: a single tensor or a list of tensors.
        `input tensor` as the single sequence of embeddings.
        [`input tensor`, `attention mask`] to have the additional attention
          mask.
        [`query tensor`, `attention mask`, `attention scores`] to have
        additional attention scores for reuse computation. If `attention scores`
        is None, the reuse_attention flag will be ignored.
    Returns:
      An output tensor with the same dimensions as input/query tensor.
      Attention scores if return_attention_scores is true.
    """
    if isinstance(inputs, (list, tuple)):
      if len(inputs) == 2:
        input_tensor, attention_mask = inputs
        reuse_attention_scores = None
      elif len(inputs) == 3:
        input_tensor, attention_mask, reuse_attention_scores = inputs
      else:
        raise ValueError("Unexpected inputs to %s with length at %d" %
                         (self.__class__, len(inputs)))
    else:
      input_tensor, attention_mask, reuse_attention_scores = (inputs, None,
                                                              None)

    key_value = None

    if self._reuse_attention != 0 and reuse_attention_scores is None:
      raise ValueError(
          "reuse_attention_scores cannot be None when reuse_attention != 0.")

    if self._output_range:
      if self._norm_first:
        source_tensor = input_tensor[:, 0:self._output_range, :]
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm(key_value)
      target_tensor = input_tensor[:, 0:self._output_range, :]
      if attention_mask is not None:
        attention_mask = attention_mask[:, 0:self._output_range, :]
      if reuse_attention_scores is not None:
        reuse_attention_scores = reuse_attention_scores[:, :,
                                                        0:self._output_range, :]
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
        query=target_tensor, value=key_value, attention_mask=attention_mask,
        reuse_attention_scores=reuse_attention_scores,
        return_attention_scores=True)
    attention_output, attention_scores = attention_output
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
      return source_attention_output + layer_output, attention_scores

    # During mixed precision training, layer norm output is always fp32 for now.
    # Casts fp32 for the subsequent add.
    layer_output = tf.cast(layer_output, tf.float32)
    layer_output = self._output_layer_norm(layer_output + attention_output)
    return layer_output, attention_scores