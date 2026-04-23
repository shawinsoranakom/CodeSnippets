def test_basic_flow(
        self,
        shuffle,
        dataset_type,
        infinite,
        workers=0,
        use_multiprocessing=False,
        max_queue_size=0,
    ):
        if use_multiprocessing and shuffle:
            pytest.skip("Starting processes is slow, test fewer variants")

        set_random_seed(1337)
        x = np.random.random((64, 4)).astype("float32")
        y = np.array([[i, i] for i in range(64)], dtype="float32")
        CPU_DEVICES = {
            "tensorflow": "CPU:0",
            "jax": "cpu:0",
        }
        cpu_device = CPU_DEVICES.get(backend.backend(), "cpu")
        with backend.device(cpu_device):
            if dataset_type == "tf":
                x, y = tf.constant(x), tf.constant(y)
            elif dataset_type == "jax":
                x, y = jax.numpy.array(x), jax.numpy.array(y)
            elif dataset_type == "torch":
                x, y = torch.as_tensor(x), torch.as_tensor(y)
        py_dataset = ExamplePyDataset(
            x,
            y,
            batch_size=16,
            workers=workers,
            use_multiprocessing=use_multiprocessing,
            max_queue_size=max_queue_size,
            infinite=infinite,
        )
        adapter = py_dataset_adapter.PyDatasetAdapter(
            py_dataset, shuffle=shuffle
        )

        if backend.backend() == "tensorflow":
            it = adapter.get_tf_dataset()
            expected_class = tf.Tensor
        elif backend.backend() == "jax":
            it = adapter.get_jax_iterator()
            expected_class = jax.Array if dataset_type == "jax" else np.ndarray
        elif backend.backend() == "torch":
            it = adapter.get_torch_dataloader()
            expected_class = torch.Tensor
        else:
            it = adapter.get_numpy_iterator()
            expected_class = np.ndarray

        sample_order = []
        adapter.on_epoch_begin()
        for batch in it:
            self.assertEqual(len(batch), 2)
            bx, by = batch
            self.assertIsInstance(bx, expected_class)
            self.assertIsInstance(by, expected_class)
            self.assertEqual(bx.dtype, by.dtype)
            self.assertContainsExactSubsequence(str(bx.dtype), "float32")
            self.assertEqual(bx.shape, (16, 4))
            self.assertEqual(by.shape, (16, 2))
            for i in range(by.shape[0]):
                sample_order.append(backend.convert_to_numpy(by[i, 0]))
            if infinite:
                if len(sample_order) == 64:
                    adapter.on_epoch_end()
                    adapter.on_epoch_begin()
                elif len(sample_order) >= 128:
                    break
        adapter.on_epoch_end()

        expected_order = list(range(64))
        if infinite:
            self.assertAllClose(sample_order, expected_order + expected_order)
        elif shuffle:
            self.assertNotAllClose(sample_order, expected_order)
            self.assertAllClose(sorted(sample_order), expected_order)
        else:
            self.assertAllClose(sample_order, expected_order)