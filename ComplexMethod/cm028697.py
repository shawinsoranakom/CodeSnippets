def __init__(
      self,
      num_attention_heads,
      inner_dim,
      inner_activation,
      output_range=None,
      kernel_initializer="glorot_uniform",
      bias_initializer="zeros",
      kernel_regularizer=None,
      bias_regularizer=None,
      activity_regularizer=None,
      kernel_constraint=None,
      bias_constraint=None,
      use_bias=True,
      norm_first=False,
      norm_epsilon=1e-12,
      use_rms_norm=False,
      output_dropout=0.0,
      attention_dropout=0.0,
      inner_dropout=0.0,
      attention_initializer=None,
      attention_axes=None,
      use_query_residual=True,
      key_dim=None,
      value_dim=None,
      output_last_dim=None,
      diff_q_kv_att_layer_norm=False,
      return_attention_scores=False,
      num_kv_heads=None,
      src_block_size=None,
      tgt_block_size=None,
      use_sigmoid_attn=False,
      sigmoid_attn_bias=None,
      linformer_dim=None,
      linformer_shared_kv_projection=True,
      lowrank_query_seq_proj_dim=None,
      enable_talking_heads=False,
      enable_gqa_optimization=False,
      softmax_robust_masking=False,
      **kwargs,
  ):
    """Initializes `TransformerEncoderBlock`.

    Note: If `output_last_dim` is used and `use_query_residual` is `True`, the
    `output_last_dim`'s value must equal the first input's last dimension for
    the query residual connection to work. This is because the residual
    connection after the multi-head-attention requires their dimensions to
    match. If `use_query_residual` is `False`, the `output_last_dim` dictactes
    the last dimension of the output of this module and the
    multi-head-attention.

    E.g. let's say input dims are `[batch_size, seq_dim, input_last_dim]`.
    Scenario 1: If `output_last_dim` is not `None`, then the output dims of this
    module would be `[batch_size, seq_dim, output_last_dim]`. Note `key_dim` is
    overridden by `output_last_dim`.
    Scenario 2: If `output_last_dim` is `None` and `key_dim` is not `None`, then
    the output dims of this module would be `[batch_size, seq_dim, key_dim]`.
    Scenario 3: If the `output_last_dim` and `key_dim` are both `None`, the
    output dims would be `[batch_size, seq_dim, input_last_dim]`.

    Args:
      num_attention_heads: Number of attention heads.
      inner_dim: The output dimension of the first Dense layer in a two-layer
        feedforward network.
      inner_activation: The activation for the first Dense layer in a two-layer
        feedforward network.
      output_range: the sequence output range, [0, output_range) for slicing the
        target sequence. `None` means the target sequence is not sliced.
      kernel_initializer: Initializer for dense layer kernels.
      bias_initializer: Initializer for dense layer biases.
      kernel_regularizer: Regularizer for dense layer kernels.
      bias_regularizer: Regularizer for dense layer biases.
      activity_regularizer: Regularizer for dense layer activity.
      kernel_constraint: Constraint for dense layer kernels.
      bias_constraint: Constraint for dense layer kernels.
      use_bias: Whether to enable use_bias in attention layer. If set False,
        use_bias in attention layer is disabled.
      norm_first: Whether to normalize inputs to attention and intermediate
        dense layers. If set False, output of attention and intermediate dense
        layers is normalized.
      norm_epsilon: Epsilon value to initialize normalization layers.
      use_rms_norm: Whether to use RMSNorm instead of LayerNorm.
      output_dropout: Dropout probability for the post-attention and output
        dropout.
      attention_dropout: Dropout probability for within the attention layer.
      inner_dropout: Dropout probability for the first Dense layer in a
        two-layer feedforward network.
      attention_initializer: Initializer for kernels of attention layers. If set
        `None`, attention layers use kernel_initializer as initializer for
        kernel.
      attention_axes: axes over which the attention is applied. `None` means
        attention over all axes, but batch, heads, and features.
      use_query_residual: Toggle to execute residual connection after attention.
      key_dim: `key_dim` for the `tf_keras.layers.MultiHeadAttention`. If
        `None`, we use the first `input_shape`'s last dim.
      value_dim: `value_dim` for the `tf_keras.layers.MultiHeadAttention`.
      output_last_dim: Final dimension of the output of this module. This also
        dictates the value for the final dimension of the multi-head-attention.
        When it's `None`, we use, in order of decreasing precedence, `key_dim` *
        `num_heads` or the first `input_shape`'s last dim as the output's last
        dim.
      diff_q_kv_att_layer_norm: If `True`, create a separate attention layer
        norm layer for query and key-value if `norm_first` is `True`. Invalid to
        set to `True` if `norm_first` is `False`.
      return_attention_scores: If `True`, the output of this layer will be a
        tuple and additionally contain the attention scores in the shape of
        `[batch_size, num_attention_heads, seq_dim, seq_dim]`.
      num_kv_heads: Number of key-value heads for multi-query attention. Refer
        to `multi_query_attention.MultiHeadAttention` for more details.
      src_block_size: Source block size. Refer to
        `block_sparse_attention.MultiHeadAttention` for more details.
      tgt_block_size: Target block size. Refer to
        `block_sparse_attention.MultiHeadAttention` for more details.
      use_sigmoid_attn: This param is only used in
        `block_sparse_attention.MultiHeadAttention`
      sigmoid_attn_bias: This param is only used in
        `block_sparse_attention.MultiHeadAttention`
      linformer_dim: Applies low-rank factorization on keys/values as in
        https://arxiv.org/pdf/2006.04768.
      linformer_shared_kv_projection: If set, projection layer is shared for
        keys and values.
      lowrank_query_seq_proj_dim: If set, applies a projection layer on query
        sequence to the given dimension. go/constformer-doc
      enable_talking_heads: Enable talking heads as in
        https://arxiv.org/pdf/2003.02436.
      enable_gqa_optimization: Enable GQA optimization in multi-query attention.
        This flag is valid only when num_kv_heads is set for GQA.
      softmax_robust_masking: If true, will use a more numerically robust
        masking impl for softmax.
      **kwargs: keyword arguments.
    """
    util.filter_kwargs(kwargs)
    super().__init__(**kwargs)

    # Deprecation warning.
    if output_range is not None:
      logging.warning("`output_range` is available as an argument for `call()`."
                      "The `output_range` as __init__ argument is deprecated.")

    self._num_heads = num_attention_heads
    self._inner_dim = inner_dim
    self._inner_activation = inner_activation
    self._attention_dropout_rate = attention_dropout
    self._output_dropout_rate = output_dropout
    self._output_range = output_range
    self._kernel_initializer = tf_keras.initializers.get(kernel_initializer)
    self._bias_initializer = tf_keras.initializers.get(bias_initializer)
    self._kernel_regularizer = tf_keras.regularizers.get(kernel_regularizer)
    self._bias_regularizer = tf_keras.regularizers.get(bias_regularizer)
    self._activity_regularizer = tf_keras.regularizers.get(activity_regularizer)
    self._kernel_constraint = tf_keras.constraints.get(kernel_constraint)
    self._bias_constraint = tf_keras.constraints.get(bias_constraint)
    self._use_bias = use_bias
    self._norm_first = norm_first
    self._norm_epsilon = norm_epsilon
    self._use_rms_norm = use_rms_norm
    self._inner_dropout = inner_dropout
    self._use_query_residual = use_query_residual
    self._key_dim = key_dim
    self._value_dim = value_dim
    self._output_last_dim = output_last_dim
    self._diff_q_kv_att_layer_norm = diff_q_kv_att_layer_norm
    self._return_attention_scores = return_attention_scores
    self._num_kv_heads = num_kv_heads
    self._src_block_size = src_block_size
    self._tgt_block_size = tgt_block_size
    self._use_sigmoid_attn = use_sigmoid_attn
    self._sigmoid_attn_bias = sigmoid_attn_bias
    self._linformer_dim = linformer_dim
    self._linformer_shared_kv_projection = linformer_shared_kv_projection
    self._lowrank_query_seq_proj_dim = lowrank_query_seq_proj_dim
    self._enable_talking_heads = enable_talking_heads
    self._enable_gqa_optimization = enable_gqa_optimization
    self._softmax_robust_masking = softmax_robust_masking
    if (
        self._src_block_size is not None
        and self._num_kv_heads is not None
        and self._num_kv_heads != 1
    ):
      raise ValueError(
          "Block sparse attention only supports Multi-query attention.Please"
          " set num_kv_heads to 1 to enable MQA with block sparse attention."
      )
    if attention_initializer:
      self._attention_initializer = tf_keras.initializers.get(
          attention_initializer
      )
    else:
      self._attention_initializer = tf_utils.clone_initializer(
          self._kernel_initializer
      )
    self._attention_axes = attention_axes

    if self._diff_q_kv_att_layer_norm and not self._norm_first:
      raise ValueError(
          "Setting `diff_q_and_kv_attention_layer_norm` to True"
          "when `norm_first` is False is invalid."
      )