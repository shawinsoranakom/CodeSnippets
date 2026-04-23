def call(self,
           inputs,
           mask,
           inverse_normalizer,
           step=None,
           beam_indices=None,
           cache=None,
           attn_mask=None):
    self._assert_rank_and_type(inputs, 3)
    self._assert_rank_and_type(mask, 3)
    assert inputs.get_shape().as_list()[-1] == self.model_dimension

    layer_out = self.dense_layers(inputs, mask, inverse_normalizer)

    # TFLite mode is handled with a custom op.
    if self.parameters.mode == base_layers.TFLITE:
      assert beam_indices is not None
      assert step is not None
      layer_out = tf_custom_ops_py.uniform_causal_attn(
          layer_out, step, beam_indices, self.model_dimension, self.beam_size)
    else:
      # Cache is used for TF Predict and Eval modes.
      if cache is None:
        attention_matrix = self.get_uniform_attention(attn_mask)
        layer_out = tf.matmul(attention_matrix, layer_out)
      else:
        assert self.parameters.mode in [base_layers.PREDICT, base_layers.EVAL]
        assert step is not None
        cache['uniform_avg'] = layer_out + cache['uniform_avg']
        layer_out = cache['uniform_avg'] / tf.cast(step, dtype=tf.float32)
    return self.qoutput(layer_out)