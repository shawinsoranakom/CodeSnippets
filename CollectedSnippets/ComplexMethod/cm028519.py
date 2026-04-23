def build(self, query_shape: Any) -> None:
    ##### Content attention
    # Einsum expression:
    #   B = batch_size
    #   N = num_heads
    #   K = head_size
    #   S = query_len (of the given attn_axis)
    #   T = key/value_len (of the given attn_axis)
    #   [U-Z] = length of other attension axes
    # Example for 5D query_heads, (e.g. images [B x H x W x N x K])
    # - when attn_axis = 0 (H axis):
    #     symbols = 'U'  => num_attn_dims = 2
    #     q_expr = 'BSUNK' => 'S' is inserted, prefix = 'B', suffix = 'NK'
    #     k_expr = 'BTUNK' => 'T' is inserted, prefix = 'B', suffix = 'NK'
    #     v_expr = 'BTUNK' => 'T' is inserted, prefix = 'B', suffix = 'NK'
    #     a_expr = 'BUNST' => 'N x S x T' attention map
    num_attn_dims = query_shape.rank - 2  # -2 to account for bsz, hidden size
    assert num_attn_dims < 6, 'Only support at most 6 attention dims.'
    symbols = ''.join([chr(ord('U') + i) for i in range(num_attn_dims - 1)])
    insert = lambda s, i, c: s[:i] + c + s[i:]
    create_expr = lambda s, prefix='B', suffix='NK': prefix + s + suffix
    self.q_expr = create_expr(insert(symbols, self.attn_axis, 'S'))
    self.k_expr = create_expr(insert(symbols, self.attn_axis, 'T'))
    self.v_expr = create_expr(insert(symbols, self.attn_axis, 'T'))
    self.a_expr = create_expr(symbols, suffix='NST')

    ##### Relative attention
    if self.rel_attn_type in ['2d_multi_head', '2d_single_head']:
      query_shape_list = query_shape.as_list()
      if query_shape.rank == 4:
        height, width = query_shape_list[1:3]
      elif query_shape.rank == 3:
        seq_len = query_shape_list[1]
        height, width = common_ops.get_shape_from_length(
            seq_len, self.input_origin_height, self.input_origin_width
        )
        if height * width != seq_len:
          raise ValueError(
              'Sequence length: %s violates input size: (%s, %s).'
              % (seq_len, height, width)
          )
      else:
        raise ValueError(
            'Does not support relative attention for query shape: %s.'
            % query_shape_list
        )

      if self.scale_ratio is not None:
        scale_ratio = eval(self.scale_ratio)  # pylint:disable=eval-used
        vocab_height = 2 * int(height / scale_ratio) - 1
        vocab_width = 2 * int(width / scale_ratio) - 1
      else:
        vocab_height = 2 * height - 1
        vocab_width = 2 * width - 1

      if self.rel_attn_type == '2d_multi_head':
        rel_bias_shape = [self.num_heads, vocab_height, vocab_width]
      elif self.rel_attn_type == '2d_single_head':
        rel_bias_shape = [vocab_height, vocab_width]
      else:
        raise NotImplementedError(
            f'rel_attn_type {self.rel_attn_type} not implemented yet.'
        )

      self._feat_height = height
      self._feat_width = width
      self.relative_bias = self.add_weight(
          'relative_bias',
          rel_bias_shape,
          initializer=self.kernel_initializer,
          trainable=True,
      )