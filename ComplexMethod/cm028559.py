def call(self, inputs: Any, output_range: Optional[tf.Tensor] = None) -> Any:
    """Transformer self-attention encoder block call.

    Args:
      inputs: a single tensor or a list of tensors. `input tensor` as the single
        sequence of embeddings. [`input tensor`, `attention mask`] to have the
        additional attention mask. [`query tensor`, `key value tensor`,
        `attention mask`] to have separate input streams for the query, and
        key/value to the multi-head attention.
      output_range: the sequence output range, [0, output_range) for slicing the
        target sequence. `None` means the target sequence is not sliced. If you
        would like to have no change to the model training, it is better to only
        set the `output_range` for serving.

    Returns:
      An output tensor with the same dimensions as input/query tensor.
    """
    if isinstance(inputs, (list, tuple)):
      if len(inputs) == 2:
        input_tensor, attention_mask = inputs
        key_value = None
      elif len(inputs) == 3:
        input_tensor, key_value, attention_mask = inputs
      else:
        raise ValueError(
            "Unexpected inputs to %s with length at %d"
            % (self.__class__, len(inputs))
        )
    else:
      input_tensor, key_value, attention_mask = (inputs, None, None)

    if output_range:
      if self._norm_first:
        source_tensor = input_tensor[:, 0:output_range, :]
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm_kv(key_value)
      target_tensor = input_tensor[:, 0:output_range, :]
      if attention_mask is not None:
        attention_mask = attention_mask[:, 0:output_range, :]
    else:
      if self._norm_first:
        source_tensor = input_tensor
        input_tensor = self._attention_layer_norm(input_tensor)
        if key_value is not None:
          key_value = self._attention_layer_norm_kv(key_value)
      target_tensor = input_tensor

    if key_value is None:
      key_value = input_tensor

    ## Low Rank Projection Here
    key = self._key_projection(key_value)
    value = self._value_projection(input_tensor)
    ## Low Rank Projection Done

    if self._return_attention_scores:
      attention_output, attention_scores = self._attention_layer(
          query=target_tensor,
          key=key,
          value=value,
          attention_mask=attention_mask,
          return_attention_scores=True,
      )
    else:
      attention_output = self._attention_layer(
          query=target_tensor,
          key=key,
          value=value,
          attention_mask=attention_mask,
      )
    attention_output = self._attention_dropout(attention_output)

    if self._norm_first:
      # Important to not combine `self._norm_first` and
      # `self._use_query_residual` into one if clause because else is only for
      # `_norm_first == False`.
      if self._use_query_residual:
        attention_output = source_tensor + attention_output
    else:
      if self._use_query_residual:
        attention_output = target_tensor + attention_output
      attention_output = self._attention_layer_norm(attention_output)

    if self._norm_first:
      source_attention_output = attention_output
      attention_output = self._output_layer_norm(attention_output)
    inner_output = self._intermediate_dense(attention_output)
    inner_output = self._intermediate_activation_layer(inner_output)
    inner_output = self._inner_dropout_layer(inner_output)
    layer_output = self._output_dense(inner_output)
    layer_output = self._output_dropout(layer_output)

    if self._norm_first:
      layer_output = source_attention_output + layer_output
    else:
      # During mixed precision training, layer norm output is always fp32 for
      # now. Casts fp32 for the subsequent add.
      layer_output = tf.cast(layer_output, tf.float32)
      layer_output = self._output_layer_norm(layer_output + attention_output)

    if self._return_attention_scores:
      return layer_output, attention_scores
    else:
      return layer_output