def __init__(
      self,
      src_block_size=None,
      tgt_block_size=None,
      use_sigmoid_attn=False,
      sigmoid_attn_bias=None,
      num_kv_heads=None,
      **kwargs
  ):
    """Initializes the block sparse attention layer.

    Args:
      src_block_size: The block size of the query. An integer that divides the
        sequence length into blocks.
      tgt_block_size: The block size of the key/value. An integer that divides
        the sequence length into blocks. The number of blocks in the source and
        target must be the same.
      use_sigmoid_attn: If enabled, uses sigmoid instead of softmax to compute
        attn probs. https://arxiv.org/pdf/2409.04431
      sigmoid_attn_bias: Bias for sigmoid attn. Suggested value -ln(seq_len).
      num_kv_heads: Number of key/value heads in the multi-head self attention.
        Refer to multi_query_attention.py for more details.
      **kwargs: Args passed to the base class.
    """
    super().__init__(**kwargs)
    if src_block_size is None or src_block_size <= 0:
      raise ValueError("src_block_size must be specified.")
    self._src_block_size = src_block_size
    self._tgt_block_size = tgt_block_size or self._src_block_size
    self._num_kv_heads = num_kv_heads
    if num_kv_heads is not None and num_kv_heads != 1:
      raise ValueError(
          "num_kv_heads must be 1. Grouped-query attention is not supported."
      )
    self._use_sigmoid_attn = use_sigmoid_attn
    self._sigmoid_attn_bias = sigmoid_attn_bias
    if self._use_sigmoid_attn:
      if self._sigmoid_attn_bias is None:
        raise ValueError(
            "sigmoid_attn_bias must be specified for sigmoid attn."
        )