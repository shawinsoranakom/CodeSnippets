def call(self, inputs, mask, inverse_normalizer, attn_mask=None):
    bsz = self.get_batch_dimension(inputs)
    self._assert_rank_and_type(inputs, 3)
    self._assert_rank_and_type(mask, 3)
    assert inputs.get_shape().as_list()[-1] == self.model_dimension

    inputs_rank2 = tf.reshape(inputs, [-1, self.model_dimension])
    mask_rank2 = tf.reshape(mask, [-1, 1])
    tensors = self.dense_layers(inputs_rank2, mask_rank2, inverse_normalizer)
    if self.parameters.mode not in [base_layers.TFLITE, base_layers.PREDICT]:
      tensors = tf.reshape(tensors, [bsz, -1, 3, self.num_heads, self.filters])
      tensors = tf.unstack(tensors, axis=2)
    else:
      tensors = tf.split(tensors, self.num_heads * 3, axis=1)
    if attn_mask is None:
      attn_mask = tf.matmul(mask, mask, transpose_b=True)
    if (self.attention_dropout_rate > 0.0 and
        self.parameters.mode == base_layers.TRAIN):
      attn_mask *= self.random_drop_to_zero(attn_mask,
                                            self.attention_dropout_rate)
    attn_mask = tf.expand_dims(attn_mask, axis=1)
    invalid_mask = (1 - attn_mask) * self.parameters.invalid_logit
    if self.parameters.mode not in [base_layers.TFLITE, base_layers.PREDICT]:
      queries = tf.transpose(tensors[0], [0, 2, 1, 3])
      keys = tf.transpose(tensors[1], [0, 2, 1, 3])
      values = tf.transpose(tensors[2], [0, 2, 1, 3])

      attn_logits = self.qactivation(tf.matmul(queries, keys, transpose_b=True))
      attn_logits_masked = attn_logits * attn_mask + invalid_mask
      attention = tf.nn.softmax(attn_logits_masked)
      attention = self.qrange_sigmoid(attention, tf_only=True)
      result = tf.matmul(attention, values)
      result = tf.transpose(result, [0, 2, 1, 3])
      result = tf.reshape(result, [bsz, -1, self.model_dimension])
      return self.qconcat([result])
    else:
      context = []
      for idx in range(self.num_heads):
        queries = tensors[idx]
        keys = tensors[idx + self.num_heads]
        values = tensors[idx + self.num_heads * 2]
        # Attention is not scaled dot product, batch normalization compensates
        # for it.
        attn_logits_masked = self.qactivation(
            tf.matmul(queries, keys, transpose_b=True))
        attention = tf.nn.softmax(attn_logits_masked)
        attention = self.qrange_sigmoid(attention, tf_only=True)
        context.append(tf.matmul(attention, values))
      result = self.qconcat(context)
      return tf.reshape(result, [1, -1, self.model_dimension])