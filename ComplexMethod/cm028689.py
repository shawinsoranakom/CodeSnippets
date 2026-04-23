def call(self, inputs, cache=None, decode_loop_step=None):
    if self.multi_channel_cross_attention:
      if len(inputs) != 5:
        raise ValueError(
            "TransformerDecoderBlock must have 5 inputs, when it uses "
            "multi_channel_cross_attention. But it got: %d" % len(inputs))
    elif len(inputs) != 4:
      raise ValueError(
          "TransformerDecoderBlock must have 4 inputs, but it got: %d" %
          len(inputs))
    input_tensor, memory, attention_mask, self_attention_mask = inputs[:4]
    source_tensor = input_tensor
    if self._norm_first:
      input_tensor = self.self_attention_layer_norm(input_tensor)
    self_attention_output, cache = self.self_attention(
        query=input_tensor,
        value=input_tensor,
        attention_mask=self_attention_mask,
        cache=cache,
        decode_loop_step=decode_loop_step)
    self_attention_output = self.self_attention_dropout(self_attention_output)
    if self._norm_first:
      self_attention_output = source_tensor + self_attention_output
    else:
      self_attention_output = self.self_attention_layer_norm(
          input_tensor + self_attention_output)
    if self._norm_first:
      source_self_attention_output = self_attention_output
      self_attention_output = self.encdec_attention_layer_norm(
          self_attention_output)
    cross_attn_inputs = dict(
        query=self_attention_output,
        value=memory,
        attention_mask=attention_mask)
    if self.multi_channel_cross_attention:
      # Accesses the 5-th input tensor for the doc-attention probabilities.
      cross_attn_inputs["context_attention_weights"] = inputs[-1]
    attention_output = self.encdec_attention(**cross_attn_inputs)

    attention_output = self.encdec_attention_dropout(attention_output)
    if self._norm_first:
      attention_output = source_self_attention_output + attention_output
    else:
      attention_output = self.encdec_attention_layer_norm(
          self_attention_output + attention_output)
    if self._norm_first:
      source_attention_output = attention_output
      attention_output = self.output_layer_norm(attention_output)

    intermediate_output = self.intermediate_dense(attention_output)
    intermediate_output = self.intermediate_activation_layer(
        intermediate_output)
    intermediate_output = self._intermediate_dropout_layer(intermediate_output)
    layer_output = self.output_dense(intermediate_output)
    layer_output = self.output_dropout(layer_output)
    if self._norm_first:
      layer_output = source_attention_output + layer_output
    else:
      layer_output = self.output_layer_norm(layer_output + attention_output)
    return layer_output, cache