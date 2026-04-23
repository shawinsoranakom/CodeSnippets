def call(self, inputs, mask, inverse_normalizer, attn_mask=None):
    batch_size = self.get_batch_dimension(inputs)
    self._assert_rank_and_type(inputs, 3)
    self._assert_rank_and_type(mask, 3)
    assert inputs.get_shape().as_list()[-1] == self.model_dimension

    inputs_rank2 = tf.reshape(inputs, [-1, self.model_dimension])
    mask_rank2 = tf.reshape(mask, [-1, 1])
    tensors = [
        layer(inputs_rank2, mask_rank2, inverse_normalizer)
        for layer in self.dense_layers
    ]
    if self.parameters.mode not in [base_layers.TFLITE, base_layers.PREDICT]:
      tensors = [
          tf.reshape(tensor, [batch_size, -1, self.filters])
          for tensor in tensors
      ]
    context = []
    if attn_mask is None:
      attn_mask = tf.matmul(mask, tf.transpose(mask, [0, 2, 1]))

    if (self.attention_dropout_rate > 0.0 and
        self.parameters.mode == base_layers.TRAIN):
      attn_mask *= self.random_drop_to_zero(attn_mask,
                                            self.attention_dropout_rate)
    invalid_mask = (1 - attn_mask) * self.parameters.invalid_logit
    for _ in range(self.num_heads):
      keys = tensors.pop()
      values = tensors.pop()
      queries = tensors.pop()
      # Attention is not scaled dot product, batch normalization compensates
      # for it.
      if self.parameters.mode not in [base_layers.TFLITE, base_layers.PREDICT]:
        queries = tf.transpose(queries, [0, 2, 1])
        attn_logits = self.qactivation(tf.matmul(keys, queries))
        attn_logits_masked = attn_logits * attn_mask + invalid_mask
        attention = tf.nn.softmax(attn_logits_masked)
        attention = self.qrange_sigmoid(attention, tf_only=True)
        context.append(tf.matmul(attention, values))
      else:
        queries = tf.transpose(queries)
        attn_logits_masked = self.qactivation(tf.matmul(keys, queries))
        attention = tf.nn.softmax(attn_logits_masked)
        attention = self.qrange_sigmoid(attention, tf_only=True)
        ctx = tf.matmul(attention, values)
        ctx = tf.reshape(ctx, [1, -1, self.filters])
        context.append(ctx)
    return self.qconcat(context)