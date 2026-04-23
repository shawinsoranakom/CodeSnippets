def call(self,
           inputs,
           input_mask,
           input_inverse_normalizer,
           memory=None,
           memory_mask=None,
           memory_inverse_normalizer=None,
           attn_mask=None):
    bsz = self.get_batch_dimension(inputs)
    self._assert_rank_and_type(inputs, 3)
    self._assert_rank_and_type(input_mask, 3)
    assert inputs.get_shape().as_list()[-1] == self.model_dimension

    inputs_rank2 = tf.reshape(inputs, [-1, self.model_dimension])
    q_tensor = self.q_dense_layers(inputs_rank2)

    if memory is not None:
      self._assert_rank_and_type(memory, 2)
      self._assert_rank_and_type(memory_mask, 2)
      if self.cached_kv:
        # Keys and Values are cached and reused at each layer.
        assert memory.get_shape().as_list()[1] == 2 * self.model_dimension
        kv_tensors = memory
      else:
        kv_tensors = self.kv_dense_layers(memory, memory_mask,
                                          memory_inverse_normalizer)
    else:
      kv_tensors = self.kv_dense_layers(inputs_rank2)
    if self.parameters.mode not in [base_layers.TFLITE, base_layers.PREDICT]:
      q_tensor = tf.reshape(q_tensor, [bsz, -1, self.num_heads, self.filters])
      kv_tensors = tf.reshape(kv_tensors,
                              [bsz, -1, 2, self.num_heads, self.filters])
      kv_tensors = tf.unstack(kv_tensors, axis=2)
    else:
      q_tensor = tf.split(q_tensor, self.num_heads, axis=1)
      kv_tensors = tf.split(kv_tensors, self.num_heads * 2, axis=1)

    if self.parameters.mode in [base_layers.TRAIN, base_layers.EVAL]:
      assert attn_mask is not None
      if (self.attention_dropout_rate > 0.0 and
          self.parameters.mode == base_layers.TRAIN):
        attn_mask *= self.random_drop_to_zero(attn_mask,
                                              self.attention_dropout_rate)
      attn_mask = tf.expand_dims(attn_mask, 1)
      invalid_mask = (1 - attn_mask) * self.parameters.invalid_logit
      queries = tf.transpose(q_tensor, [0, 2, 1, 3])
      keys = tf.transpose(kv_tensors[0], [0, 2, 1, 3])
      values = tf.transpose(kv_tensors[1], [0, 2, 1, 3])

      attn_logits = self.qactivation(tf.matmul(queries, keys, transpose_b=True))
      attn_logits_masked = attn_logits * attn_mask + invalid_mask
      attention = tf.nn.softmax(attn_logits_masked)
      attention = self.qrange_sigmoid(attention, tf_only=True)
      result = tf.matmul(attention, values)
      result = tf.transpose(result, [0, 2, 1, 3])
      result = tf.reshape(result, [bsz, -1, self.model_dimension])
      return self.qconcat([result])
    else:
      # We need to invoke the keras layer before calling APIs that it provides
      # such as quantize_using_range.
      self.qconcat(None)
      context = []
      for head in range(self.num_heads):
        queries = q_tensor[head]
        if self.parameters.mode == base_layers.PREDICT:
          # PREDICT mode assumes callers tile and merge beam size with batch
          # size. Hence extracting the first entry in the tile to compute
          # attention.
          keys = tf.split(kv_tensors[head], bsz, axis=0)
          keys = keys[0]
          values = tf.split(kv_tensors[head + self.num_heads], bsz, axis=0)
          values = values[0]
        else:
          keys = kv_tensors[head]
          values = kv_tensors[head + self.num_heads]
        attn_logits_masked = self.qactivation(
            tf.matmul(queries, keys, transpose_b=True))
        attention = tf.nn.softmax(attn_logits_masked)
        attention = self.qrange_sigmoid(attention, tf_only=True)
        context.append(
            self.qconcat.quantize_using_range(tf.matmul(attention, values)))
      # Concatenating heads along axis 1.
      result = self.qconcat.quantize_using_range(tf.concat(context, axis=1))
      return tf.reshape(result, [-1, 1, self.model_dimension])