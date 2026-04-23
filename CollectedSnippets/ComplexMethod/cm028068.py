def call(self, inputs, seq_length):
    """Performs downsampling on the character-scale input representation.

    Based in principle on https://arxiv.org/pdf/2106.12672.pdf.

    Args:
      inputs: float Tensor of shape [batch_size, seq_length, embedding_size].
      seq_length: sequence length of shape [batch_size].

    Returns:
      <float>[batch_size, seq_length / downsample_rate, embedding_size].
        Downsampled sequences.
    """
    self._assert_rank_and_type(inputs, 3)
    bsz = self.get_batch_dimension(inputs)
    max_seq_len = self.max_seq_len

    if self.parameters.mode in [base_layers.PREDICT, base_layers.TFLITE]:
      num_steps = tf.shape(inputs)[1]

    inputs = self.zero_pad(inputs)
    inputs = self.conv_layer(inputs)

    all_block_scores = []
    all_sequences = []
    for subword_len in self.subword_blocks_width:
      if self.add_block_pos_embed:
        block_pos_indices = tf.range(subword_len, dtype=tf.int32)
        block_pos_indices = tf.reshape(block_pos_indices, [1, -1])
        block_pos_embeds = self.block_pos_embedding(block_pos_indices)
        tile_len = math.ceil(max_seq_len / float(subword_len))
        retiled_block_pos_embeds = tf.repeat(block_pos_embeds, tile_len, axis=1)
        inputs += retiled_block_pos_embeds
      # For this block size, form candidate block embeddings and scores.
      # candidates shape: [batch, seq_len/subword_len, dim]
      # block_scores shape: [batch, seq_len/subword_len, 1]
      candidates = tf.nn.avg_pool(
          inputs, [subword_len], strides=[subword_len], padding="SAME")
      candidates = self.conv_layer.quantize_using_output_range(candidates)

      block_scores = self.block_attn(candidates)
      # Upsample it back to the original sequence length.
      retiled_seq = tf.repeat(candidates, subword_len, axis=1)
      retiled_block_scores = tf.repeat(block_scores, subword_len, axis=1)

      # Make sure everything is the right length and add new dimension to concat
      # candidate blocks on.
      if self.parameters.mode in [base_layers.PREDICT, base_layers.TFLITE]:
        retiled_block_scores = retiled_block_scores[:, :num_steps, :]
        retiled_seq = retiled_seq[:, :num_steps, :]
      else:
        retiled_block_scores = retiled_block_scores[:, :max_seq_len, :]
        retiled_seq = retiled_seq[:, :max_seq_len, :]
      retiled_seq = tf.expand_dims(retiled_seq, axis=-1)
      retiled_block_scores = tf.expand_dims(retiled_block_scores, axis=-1)
      all_sequences.append(retiled_seq)
      all_block_scores.append(retiled_block_scores)

    block_net = self.scores_concat(all_block_scores)
    if self.block_mixing_mode == "score_attention":
      if self.parameters.mode in [base_layers.PREDICT, base_layers.TFLITE]:
        block_attn_steps = []
        self.attn_concat(None)
        for i in range(num_steps):
          block_i = tf.reshape(block_net[:, i:i + 1, :, :], [1, -1])
          block_attn_steps.append(tf.matmul(block_i, block_i, transpose_b=True))
        block_attn = self.attn_concat(block_attn_steps)
        block_attn = tf.reshape(block_attn, [bsz, -1, 1, 1])
      else:
        block_attn = self.attn_concat(
            [tf.matmul(block_net, block_net, transpose_b=True)])

      block_attn = tf.nn.softmax(block_attn, axis=1)
      block_attn = self.qrange_sigmoid(block_attn, tf_only=True)
      block_net_scaled = self.qact(block_attn * block_net)
    else:
      block_net_scaled = block_net

    candidate_embeds = self.conv_layer.quantize_using_output_range(
        tf.concat(all_sequences, axis=3))
    dot_product = self.qact_dot(block_net_scaled * candidate_embeds)
    output = self.qoutput(tf.reduce_mean(dot_product, axis=-1, keepdims=True))
    output = tf.reshape(output, [bsz, -1, self.feature_size])

    # Removing pad entries for inference mode.
    if self.parameters.mode in [base_layers.PREDICT, base_layers.TFLITE]:
      output = output[:, :num_steps, :]
    # Downsample by mean pooling.
    if self.downsample_rate > 1:
      output = tf.nn.avg_pool(
          output, (self.downsample_rate,),
          strides=(self.downsample_rate,),
          padding="VALID")
    return output