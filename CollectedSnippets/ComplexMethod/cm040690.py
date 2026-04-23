def test_basic_flow(self, use_sample_weight, generator_type):
        x = np.random.random((34, 4)).astype("float32")
        y = np.array([[i, i] for i in range(34)], dtype="float32")
        sw = np.random.random((34,)).astype("float32")
        if generator_type == "tf":
            x, y, sw = tf.constant(x), tf.constant(y), tf.constant(sw)
        elif generator_type == "jax":
            x, y, sw = jnp.array(x), jnp.array(y), jnp.array(sw)
        elif generator_type == "torch":
            x, y, sw = (
                torch.as_tensor(x),
                torch.as_tensor(y),
                torch.as_tensor(sw),
            )
        if not use_sample_weight:
            sw = None
        make_generator = example_generator(
            x,
            y,
            sample_weight=sw,
            batch_size=16,
        )

        adapter = generator_data_adapter.GeneratorDataAdapter(make_generator())
        if backend.backend() == "tensorflow":
            it = adapter.get_tf_dataset()
            expected_class = tf.Tensor
        elif backend.backend() == "jax":
            it = adapter.get_jax_iterator()
            expected_class = (
                jax.Array if generator_type == "jax" else np.ndarray
            )
        elif backend.backend() == "torch":
            it = adapter.get_torch_dataloader()
            expected_class = torch.Tensor
        else:
            it = adapter.get_numpy_iterator()
            expected_class = np.ndarray

        sample_order = []
        for i, batch in enumerate(it):
            if use_sample_weight:
                self.assertEqual(len(batch), 3)
                bx, by, bsw = batch
            else:
                self.assertEqual(len(batch), 2)
                bx, by = batch
            self.assertIsInstance(bx, expected_class)
            self.assertIsInstance(by, expected_class)
            self.assertEqual(bx.dtype, by.dtype)
            self.assertContainsExactSubsequence(str(bx.dtype), "float32")
            if i < 2:
                self.assertEqual(bx.shape, (16, 4))
                self.assertEqual(by.shape, (16, 2))
            else:
                self.assertEqual(bx.shape, (2, 4))
                self.assertEqual(by.shape, (2, 2))
            if use_sample_weight:
                self.assertIsInstance(bsw, expected_class)
            for j in range(by.shape[0]):
                sample_order.append(backend.convert_to_numpy(by[j, 0]))
        self.assertAllClose(sample_order, list(range(34)))