def _build_from_signature(self, query, value, key=None):
    # pytype: disable=attribute-error
    super()._build_from_signature(query, value, key)
    # pytype: enable=attribute-error
    # If block sizes are same as sequence lengths, we defer to default attn.
    if (
        self._query_shape[-2] == self._src_block_size
        and self._key_shape[-2] == self._tgt_block_size
    ):
      return
    # The following capital letters are used to denote the tensor dimension
    # parameters:
    # B = batch size
    # S = length of the key/value (target)
    # D = model dimension.
    # T = length of the query (source)
    # t = block size of the source.
    # s = block size of the target.
    # L = number of blocks in the source/target.
    # N = number of attention heads
    # H = dimensions of each attention head.
    with tf.init_scope():
      proj_einsum_eqn = "BTD,DNH->BNTH"
      bias_axes = "NH"
      qk_output_shape = [
          self._num_heads,
          None,
          self._key_dim,
      ]
      v_output_shape = [
          self._num_heads,
          None,
          self._value_dim,
      ]
      self._query_dense = tf_keras.layers.EinsumDense(
          proj_einsum_eqn,
          output_shape=qk_output_shape,
          bias_axes=bias_axes if self._use_bias else None,
          name="query",
          **self._get_common_kwargs_for_sublayer(),
      )
      if self._num_kv_heads == 1:
        self._key_dense = tf_keras.layers.EinsumDense(
            "BTD,DH->BTH",
            output_shape=[None, self._key_dim],
            bias_axes="H" if self._use_bias else None,
            name="key",
            **self._get_common_kwargs_for_sublayer(),
        )
        self._value_dense = tf_keras.layers.EinsumDense(
            "BTD,DH->BTH",
            output_shape=[None, self._value_dim],
            bias_axes="H" if self._use_bias else None,
            name="value",
            **self._get_common_kwargs_for_sublayer(),
        )
      else:
        self._key_dense = tf_keras.layers.EinsumDense(
            proj_einsum_eqn,
            output_shape=qk_output_shape,
            bias_axes=bias_axes if self._use_bias else None,
            name="key",
            **self._get_common_kwargs_for_sublayer(),
        )
        self._value_dense = tf_keras.layers.EinsumDense(
            proj_einsum_eqn,
            output_shape=v_output_shape,
            bias_axes=bias_axes if self._use_bias else None,
            name="value",
            **self._get_common_kwargs_for_sublayer(),
        )
      if self._key_shape[-2] == self._tgt_block_size:
        if self._num_kv_heads == 1:
          self._dot_product_equation = "BsH,BNLtH->BNLts"
          self._combine_equation = "BNLts,BsH->BNLtH"
        else:
          self._dot_product_equation = "BNsH,BNLtH->BNLts"
          self._combine_equation = "BNLts,BNsH->BNLtH"
      else:
        if self._num_kv_heads == 1:
          self._dot_product_equation = "BLsH,BNLtH->BNLts"
          self._combine_equation = "BNLts,BLsH->BNLtH"
        else:
          self._dot_product_equation = "BNLsH,BNLtH->BNLts"
          self._combine_equation = "BNLts,BNLsH->BNLtH"
      if self._output_shape:
        if not isinstance(self._output_shape, collections.abc.Sized):
          output_shape = [self._output_shape]
        else:
          output_shape = self._output_shape
      else:
        output_shape = [self._query_shape[-1]]
      output_shape = [None] + output_shape
      self._output_dense = tf_keras.layers.EinsumDense(
          "BNTH,DNH->BTD",
          output_shape=output_shape,
          bias_axes="D" if self._use_bias else None,
          name="attention_output",
          **self._get_common_kwargs_for_sublayer(),
      )