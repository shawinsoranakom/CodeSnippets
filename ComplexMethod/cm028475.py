def call(self, inputs):
    """Implements call() for the layer."""
    inp_k = inputs["inp_k"]
    seg_id = inputs["seg_id"]
    input_mask = inputs["input_mask"]
    mems = inputs["mems"]
    perm_mask = inputs["perm_mask"]
    target_mapping = inputs["target_mapping"]
    inp_q = inputs["inp_q"]

    new_mems = []

    bsz = tf.shape(inp_k)[1]

    qlen = inp_k.shape.as_list()[0]

    mlen = mems[0].shape.as_list()[0] if mems is not None else 0
    klen = mlen + qlen

    ##### Attention mask
    # causal attention mask
    if self.attn_type == "uni":
      attn_mask = _create_mask(qlen, mlen, self.tf_float, self.same_length)
      # pylint: enable=protected-access
      attn_mask = attn_mask[:, :, None, None]
    elif self.attn_type == "bi":
      attn_mask = None
    else:
      raise ValueError("Unsupported attention type: {}".format(self.attn_type))

    # data mask: input mask & perm mask
    if input_mask is not None and perm_mask is not None:
      data_mask = input_mask[None] + perm_mask

    elif input_mask is not None and perm_mask is None:
      data_mask = input_mask[None]
    elif input_mask is None and perm_mask is not None:
      data_mask = perm_mask
    else:
      data_mask = None

    if data_mask is not None:
      # all mems can be attended to
      mems_mask = tf.zeros([tf.shape(data_mask)[0], mlen, bsz],
                           dtype=self.tf_float)
      data_mask = tf.concat([mems_mask, data_mask], 1)
      if attn_mask is None:
        attn_mask = data_mask[:, :, :, None]
      else:
        attn_mask += data_mask[:, :, :, None]

    if attn_mask is not None:
      attn_mask = tf.cast(attn_mask > 0, dtype=self.tf_float)

    if attn_mask is not None:
      non_tgt_mask = -tf.eye(qlen, dtype=self.tf_float)
      non_tgt_mask = tf.concat(
          [tf.zeros([qlen, mlen], dtype=self.tf_float), non_tgt_mask], axis=-1)
      non_tgt_mask = tf.cast(
          (attn_mask + non_tgt_mask[:, :, None, None]) > 0, dtype=self.tf_float)
    else:
      non_tgt_mask = None

    word_emb_k = self.embedding_lookup(inp_k)

    if inp_q is not None:
      if target_mapping is not None:
        word_emb_q = tf.tile(self.mask_emb,
                             [tf.shape(target_mapping)[0], bsz, 1])
      else:
        inp_q_ext = inp_q[:, :, None]
        word_emb_q = inp_q_ext * self.mask_emb + (1 - inp_q_ext) * word_emb_k

    output_h = self.h_dropout(word_emb_k)
    output_g = None
    if inp_q is not None:
      output_g = self.g_dropout(word_emb_q)

    ##### Segment embedding
    if seg_id is not None:

      # Convert `seg_id` to one-hot `seg_mat`

      mem_pad = tf.zeros([mlen, bsz], dtype=tf.int32)

      cat_id = tf.concat([mem_pad, seg_id], 0)

      if self.use_cls_mask:
        # `1` indicates not in the same segment [qlen x klen x bsz]
        # seg_id: [qlen x bsz] & cat_id: [klen x bsz]
        cls_mat = tf.logical_or(
            tf.equal(seg_id, tf.constant([data_utils.SEG_ID_CLS]))[:, None],
            tf.equal(cat_id, tf.constant([data_utils.SEG_ID_CLS]))[None, :])
        seg_mat = tf.equal(seg_id[:, None], cat_id[None, :])
        seg_mat = tf.logical_or(cls_mat, seg_mat)
      else:
        seg_mat = tf.logical_not(tf.equal(seg_id[:, None], cat_id[None, :]))
    else:
      seg_mat = None

    dtype = self.tf_float
    freq_seq = tf.range(0, self.d_model, 2.0)
    if dtype is not None and dtype != tf.float32:
      freq_seq = tf.cast(freq_seq, dtype=self.dtype)

    if self.attn_type == "bi":
      beg, end = klen, -qlen
    elif self.attn_type == "uni":
      beg, end = klen, -1
    else:
      raise ValueError("Unknown `attn_type` {}.".format(self.attn_type))

    if self.bi_data:
      fwd_pos_seq = tf.range(beg, end, -1.0)
      bwd_pos_seq = tf.range(-beg, -end, 1.0)

      if dtype is not None and dtype != tf.float32:
        fwd_pos_seq = tf.cast(fwd_pos_seq, dtype=dtype)
        bwd_pos_seq = tf.cast(bwd_pos_seq, dtype=dtype)

      if self.clamp_len > 0:
        fwd_pos_seq = tf.clip_by_value(fwd_pos_seq, -self.clamp_len,
                                       self.clamp_len)
        bwd_pos_seq = tf.clip_by_value(bwd_pos_seq, -self.clamp_len,
                                       self.clamp_len)

      if bsz is not None:
        fwd_pos_emb = self.fwd_position_embedding(fwd_pos_seq, bsz // 2)
        bwd_pos_emb = self.bwd_position_embedding(bwd_pos_seq, bsz // 2)
      else:
        fwd_pos_emb = self.fwd_position_embedding(fwd_pos_seq, None)
        bwd_pos_emb = self.bwd_position_embedding(bwd_pos_seq, None)

      pos_emb = tf.concat([fwd_pos_emb, bwd_pos_emb], axis=1)
    else:
      fwd_pos_seq = tf.range(beg, end, -1.0)
      if dtype is not None and dtype != tf.float32:
        fwd_pos_seq = tf.cast(fwd_pos_seq, dtype=dtype)
      if self.clamp_len > 0:
        fwd_pos_seq = tf.clip_by_value(fwd_pos_seq, -self.clamp_len,
                                       self.lamp_len)

      pos_emb = self.fwd_position_embedding(fwd_pos_seq, bsz)

    pos_emb = self.emb_dropout(pos_emb)

    if mems is None:
      mems = [None] * self.n_layer
    for i in range(self.n_layer):
      # cache new mems
      new_mems.append(
          _cache_mem(output_h, mems[i], self.mem_len, self.reuse_len))
      # pylint: enable=protected-access

      # segment bias
      if seg_id is None:
        r_s_bias_i = None
        seg_embed_i = None
      else:
        r_s_bias_i = self.r_s_bias if not self.untie_r else self.r_s_bias[i]
        seg_embed_i = self.seg_embed[i]

      ffn_layer = self.h_positionwise_ffn_layers[i]
      attention_layer = self.rel_multihead_layers[i]
      output_h, output_g = attention_layer(
          h=output_h,
          g=output_g,
          r=pos_emb,
          r_w_bias=self.r_w_bias if not self.untie_r else self.r_w_bias[i],
          r_r_bias=self.r_r_bias if not self.untie_r else self.r_r_bias[i],
          seg_mat=seg_mat,
          r_s_bias=r_s_bias_i,
          seg_embed=seg_embed_i,
          attn_mask_h=non_tgt_mask,
          attn_mask_g=attn_mask,
          mems=mems[i],
          target_mapping=target_mapping)
      output_h = ffn_layer(output_h)
      if output_g is not None:
        output_g = ffn_layer(output_g)

    if inp_q is not None:
      output = output_g
    else:
      output = output_h

    return output, new_mems, None