def test_masked_attention(self, use_bias, reuse_attention):
    """Test with a mask tensor."""
    test_layer = attention.ReuseMultiHeadAttention(
        num_heads=2, key_dim=2, use_bias=use_bias,
        reuse_attention=reuse_attention)
    # Create a 3-dimensional input (the first dimension is implicit).
    batch_size = 3
    query = tf_keras.Input(shape=(4, 8))
    value = tf_keras.Input(shape=(2, 8))
    mask_tensor = tf_keras.Input(shape=(4, 2))
    reuse_attention_scores = tf_keras.Input(shape=(2, 4, 2))
    output = test_layer(query=query, value=value, attention_mask=mask_tensor,
                        reuse_attention_scores=reuse_attention_scores)
    # Create a model containing the test layer.
    model = tf_keras.Model(
        [query, value, mask_tensor, reuse_attention_scores], output)

    # Generate data for the input (non-mask) tensors.
    from_data = 10 * np.random.random_sample((batch_size, 4, 8))
    to_data = 10 * np.random.random_sample((batch_size, 2, 8))
    reuse_scores = np.random.random_sample((batch_size, 2, 4, 2))
    # Invoke the data with a random set of mask data. This should mask at least
    # one element.
    mask_data = np.random.randint(2, size=(batch_size, 4, 2))
    masked_output_data = model.predict(
        [from_data, to_data, mask_data, reuse_scores])

    # Invoke the same data, but with a null mask (where no elements are masked).
    null_mask_data = np.ones((batch_size, 4, 2))
    unmasked_output_data = model.predict(
        [from_data, to_data, null_mask_data, reuse_scores])

    # Because one data is masked and one is not, the outputs should not be the
    # same.
    if reuse_attention == -1:
      self.assertAllEqual(masked_output_data, unmasked_output_data)
    else:
      self.assertNotAllClose(masked_output_data, unmasked_output_data)

    # Tests the layer with three inputs: Q, K, V.
    key = tf_keras.Input(shape=(2, 8))
    output = test_layer(query, value=value, key=key, attention_mask=mask_tensor,
                        reuse_attention_scores=reuse_attention_scores)
    model = tf_keras.Model(
        [query, value, key, mask_tensor, reuse_attention_scores], output)

    masked_output_data = model.predict(
        [from_data, to_data, to_data, mask_data, reuse_scores])
    unmasked_output_data = model.predict(
        [from_data, to_data, to_data, null_mask_data, reuse_scores])
    # Because one data is masked and one is not, the outputs should not be the
    # same.
    if reuse_attention == -1:
      self.assertAllEqual(masked_output_data, unmasked_output_data)
    else:
      self.assertNotAllClose(masked_output_data, unmasked_output_data)
    if reuse_attention > 0:
      self.assertLen(test_layer._output_dense, 2)
    if use_bias:
      if reuse_attention == 0:
        self.assertLen(test_layer._query_dense.trainable_variables, 2)
      self.assertLen(test_layer._output_dense[0].trainable_variables, 2)
      if len(test_layer._output_dense) == 2:
        self.assertLen(test_layer._output_dense[1].trainable_variables, 1)
    else:
      if reuse_attention == 0:
        self.assertLen(test_layer._query_dense.trainable_variables, 1)
      self.assertLen(test_layer._output_dense[0].trainable_variables, 1)
      if len(test_layer._output_dense) == 2:
        self.assertLen(test_layer._output_dense[1].trainable_variables, 1)