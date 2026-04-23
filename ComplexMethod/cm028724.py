def test_network_creation(self, expected_dtype):
    hidden_size = 32
    sequence_length = 21

    kwargs = dict(
        vocab_size=100,
        hidden_size=hidden_size,
        num_attention_heads=2,
        num_layers=3)
    if expected_dtype == tf.float16:
      tf_keras.mixed_precision.set_global_policy("mixed_float16")

    # Create a small TransformerEncoder for testing.
    test_network = albert_encoder.AlbertEncoder(**kwargs)

    # Create the inputs (note that the first dimension is implicit).
    word_ids = tf_keras.Input(shape=(sequence_length,), dtype=tf.int32)
    mask = tf_keras.Input(shape=(sequence_length,), dtype=tf.int32)
    type_ids = tf_keras.Input(shape=(sequence_length,), dtype=tf.int32)
    data, pooled = test_network([word_ids, mask, type_ids])

    expected_data_shape = [None, sequence_length, hidden_size]
    expected_pooled_shape = [None, hidden_size]
    self.assertAllEqual(expected_data_shape, data.shape.as_list())
    self.assertAllEqual(expected_pooled_shape, pooled.shape.as_list())

    # If float_dtype is set to float16, the data output is float32 (from a layer
    # norm) and pool output should be float16.
    self.assertEqual(tf.float32, data.dtype)
    self.assertEqual(expected_dtype, pooled.dtype)

    # ALBERT has additonal 'embedding_hidden_mapping_in' weights and
    # it shares transformer weights.
    self.assertNotEmpty(
        [x for x in test_network.weights if "embedding_projection/" in x.name])
    self.assertNotEmpty(
        [x for x in test_network.weights if "transformer/" in x.name])
    self.assertEmpty(
        [x for x in test_network.weights if "transformer/layer" in x.name])