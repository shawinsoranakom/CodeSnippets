def call(
      self,
      inputs: tf.Tensor,
      training: Optional[bool] = None
  ) -> Union[tf.Tensor, Tuple[tf.Tensor, tf.Tensor]]:
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

    if self._norm_first:
      source_tensor = input_tensor
      input_tensor = self._attention_layer_norm(input_tensor)

    if key_value is None:
      key_value = input_tensor

    attention_output, attention_scores = self._attention_layer(
        query=input_tensor,
        value=key_value,
        attention_mask=attention_mask,
        training=training,
        return_attention_scores=True)
    attention_output = self._attention_dropout(
        attention_output, training=training)

    if self._norm_first:
      source_attention_output = source_tensor + self._stochastic_depth(
          attention_output, training=training)
      attention_output = self._output_layer_norm(
          source_attention_output)
    else:
      attention_output = self._attention_layer_norm(
          input_tensor +
          self._stochastic_depth(attention_output, training=training))

    if self._feedforward_block is None:
      intermediate_output = self._intermediate_dense(attention_output)
      intermediate_output = self._intermediate_activation_layer(
          intermediate_output)
      layer_output = self._output_dense(intermediate_output)
      layer_output = self._output_dropout(layer_output, training=training)
    else:
      layer_output = self._feedforward_block(
          attention_output, training=training)

    if self._norm_first:
      if self._ffn_has_residual_connection:
        raise ValueError(
            'In the case of `norm_first`, the residual connection should be'
            "done in the TransformerScaffold call function, not FFN's"
            'call function.')
      output = source_attention_output + self._stochastic_depth(
          layer_output, training=training)
    else:
      # During mixed precision training, layer norm output is always fp32 for
      # now. Casts fp32 for the subsequent add.
      layer_output = tf.cast(layer_output, tf.float32)
      if self._ffn_has_residual_connection:
        output = self._stochastic_depth(layer_output, training=training)
      else:
        output = self._output_layer_norm(
            attention_output +
            self._stochastic_depth(layer_output, training=training))

    if self._return_attention_scores:
      return output, attention_scores
    else:
      return output