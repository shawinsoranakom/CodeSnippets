def call(self,
           content_stream,
           relative_position_encoding,
           segment_matrix=None,
           segment_embedding=None,
           state=None,
           content_attention_mask=None,
           query_stream=None,
           query_attention_mask=None,
           target_mapping=None):
    """Implements call() for the layer.

    Args:
      content_stream: `Tensor`, the input content stream. This is the standard
        input to Transformer XL and is commonly referred to as `h` in XLNet.
      relative_position_encoding: Relative positional encoding `Tensor` of shape
        `[B, L, dim]`.
      segment_matrix: Optional `Tensor` of shape `[B, S, S + M]`. Used in XLNet,
        but not in Transformer XL.
      segment_embedding: Optional `Tensor` of shape `[2, num_heads, dim]`. Used
        in XLNet, but not in Transformer XL.
      state: Optional `Tensor` of shape `[B, M, E]`, where M is the length of
        the state or memory. If passed, this is also attended over as in
        Transformer XL.
      content_attention_mask: Optional `Tensor` representing the mask that is
        added to content attention logits. If state is not None, the mask source
        sequence dimension should extend M.
      query_stream: Optional `Tensor`, the query stream. This is introduced in
        `TwoStreamRelativeAttention`/XLNet pretrainer. This is ignored if
        `two_stream` is `False`.
      query_attention_mask: Optional `Tensor` representing the mask that is
        added to query attention logits. If state is not None, the mask source
        sequence dimension should extend M.
      target_mapping: Optional `Tensor` representing the target mapping when
        calculating query attention.

    Returns:
      A tuple consisting of the attention output and the list of cached memory
      states.
      The attention output is `content_attention` if `two_stream` is `False`,
      otherwise it is `query_attention`.
    """
    new_mems = []

    if state is None:
      state = [None] * self._num_layers
    for i in range(self._num_layers):
      # cache new mems
      new_mems.append(
          _cache_memory(content_stream, state[i],
                        self._memory_length, self._reuse_length))

      # segment bias
      if segment_matrix is None:
        segment_attention_bias = None
        segment_encoding = None
      else:
        segment_attention_bias = (self.segment_attention_bias
                                  if self._tie_attention_biases
                                  else self.segment_attention_bias[i])
        segment_encoding = segment_embedding[i]

      content_attention_bias = (self.content_attention_bias
                                if self._tie_attention_biases
                                else self.content_attention_bias[i])
      positional_attention_bias = (self.positional_attention_bias
                                   if self._tie_attention_biases
                                   else self.positional_attention_bias[i])
      transformer_xl_layer = self.transformer_xl_layers[i]
      transformer_xl_output = transformer_xl_layer(
          content_stream=content_stream,
          content_attention_bias=content_attention_bias,
          positional_attention_bias=positional_attention_bias,
          relative_position_encoding=relative_position_encoding,
          segment_matrix=segment_matrix,
          segment_encoding=segment_encoding,
          segment_attention_bias=segment_attention_bias,
          state=state[i],
          content_attention_mask=content_attention_mask,
          query_attention_mask=query_attention_mask,
          query_stream=query_stream,
          target_mapping=target_mapping)
      content_stream = transformer_xl_output["content_attention"]
      if self._two_stream:
        query_stream = transformer_xl_output["query_attention"]
      else:
        query_stream = None

    if self._two_stream:
      output_stream = query_stream
    else:
      output_stream = content_stream

    return output_stream, new_mems