def test_dataloader_iterable_dataset(self, batch_size, implements_len):
        class TestIterableDataset(torch.utils.data.IterableDataset):
            def __init__(self):
                self.x = torch.normal(2, 3, size=(16, 4))
                self.y = torch.normal(1, 3, size=(16, 2))

            def __iter__(self):
                for _ in range(10):
                    yield (self.x, self.y)

        class TestIterableDatasetWithLen(TestIterableDataset):
            def __len__(self):
                return 10

        ds = (
            TestIterableDatasetWithLen()
            if implements_len
            else TestIterableDataset()
        )
        dataloader = torch.utils.data.DataLoader(ds, batch_size=batch_size)
        adapter = TorchDataLoaderAdapter(dataloader)

        if implements_len and batch_size:
            self.assertEqual(adapter.num_batches, math.ceil(10 / batch_size))
            self.assertEqual(adapter.batch_size, batch_size)
            self.assertEqual(adapter.has_partial_batch, True)
            self.assertEqual(adapter.partial_batch_size, 10 % batch_size)
        elif implements_len:
            self.assertEqual(adapter.num_batches, 10)
            self.assertEqual(adapter.batch_size, None)
            self.assertEqual(adapter.has_partial_batch, None)
            self.assertEqual(adapter.partial_batch_size, None)
        else:
            self.assertIsNone(adapter.num_batches)
            self.assertEqual(adapter.batch_size, batch_size)
            self.assertIsNone(adapter.has_partial_batch)
            self.assertIsNone(adapter.partial_batch_size)

        if backend.backend() == "tensorflow":
            it = adapter.get_tf_dataset()
            expected_class = tf.Tensor
        elif backend.backend() == "jax":
            it = adapter.get_jax_iterator()
            expected_class = np.ndarray
        elif backend.backend() == "torch":
            it = adapter.get_torch_dataloader()
            expected_class = torch.Tensor
        else:
            it = adapter.get_numpy_iterator()
            expected_class = np.ndarray

        batch_count = 0
        for i, batch in enumerate(it):
            batch_count += 1
            self.assertEqual(len(batch), 2)
            bx, by = batch
            self.assertIsInstance(bx, expected_class)
            self.assertIsInstance(by, expected_class)
            self.assertEqual(bx.dtype, by.dtype)
            self.assertContainsExactSubsequence(str(bx.dtype), "float32")
            if batch_size:
                if i < 3:
                    self.assertEqual(bx.shape, (batch_size, 16, 4))
                    self.assertEqual(by.shape, (batch_size, 16, 2))
                else:
                    self.assertEqual(bx.shape, (10 % batch_size, 16, 4))
                    self.assertEqual(by.shape, (10 % batch_size, 16, 2))
            else:
                self.assertEqual(bx.shape, (16, 4))
                self.assertEqual(by.shape, (16, 2))

        if batch_size:
            self.assertEqual(batch_count, math.ceil(10 / batch_size))
        else:
            self.assertEqual(batch_count, 10)