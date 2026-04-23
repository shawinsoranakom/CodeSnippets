def build(self, input_shape):
    """Create layer state."""
    self._input_norm = self._norm(
        axis=self._bn_axis,
        momentum=self._norm_momentum,
        epsilon=self._norm_epsilon,
    )

    # This CPE is different than the one suggested in the original paper.
    # https://arxiv.org/abs/2102.10882
    # 1. Rather than adding one CPE before the attention blocks, we add a CPE
    #    into every attention block.
    # 2. We replace the expensive Conv2D by a Seperable DW Conv.
    if self._use_cpe:
      self._cpe_dw_conv = tf_keras.layers.DepthwiseConv2D(
          kernel_size=self._cpe_dw_kernel_size,
          strides=1,
          padding='same',
          depth_multiplier=1,
          use_bias=True,
      )

    # TODO(qind): assert feature dim dividable by 32
    if self._num_heads is None:
      num_heads = self._input_dim // self._key_dim
    else:
      num_heads = self._num_heads
    if self._use_multi_query:
      if (
          self._query_h_strides > 1
          or self._query_w_strides > 1
          or self._kv_strides > 1
      ):
        self._multi_query_attention = (
            OptimizedMultiQueryAttentionLayerWithDownSampling(
                num_heads=num_heads,
                key_dim=self._key_dim,
                value_dim=self._value_dim,
                query_h_strides=self._query_h_strides,
                query_w_strides=self._query_w_strides,
                kv_strides=self._kv_strides,
                dw_kernel_size=self._downsampling_dw_kernel_size,
                dropout=self._dropout,
            )
        )
      else:
        self._multi_query_attention = MultiQueryAttentionLayerV2(
            num_heads=num_heads,
            key_dim=self._key_dim,
            value_dim=self._value_dim,
            dropout=self._dropout,
        )
    else:
      self._multi_head_attention = tf_keras.layers.MultiHeadAttention(
          num_heads=num_heads,
          key_dim=self._key_dim,
          dropout=self._dropout,
          use_bias=self._use_bias,
      )

    if self._use_layer_scale:
      self._layer_scale = MNV4LayerScale(self._layer_scale_init_value)

    if self._stochastic_depth_drop_rate:
      self._stochastic_depth = nn_layers.StochasticDepth(
          self._stochastic_depth_drop_rate
      )
    else:
      self._stochastic_depth = None

    super().build(input_shape)