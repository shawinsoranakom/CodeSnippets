def test_basic_flow(self, array_type, array_dtype, shuffle):
        x = self.make_array(array_type, (34, 4), array_dtype)
        y = self.make_array(array_type, (34, 2), "int32")
        xdim1 = 1 if array_type == "pandas_series" else 4
        ydim1 = 1 if array_type == "pandas_series" else 2

        adapter = array_data_adapter.ArrayDataAdapter(
            x,
            y=y,
            sample_weight=None,
            batch_size=16,
            steps=None,
            shuffle=shuffle,
        )
        self.assertEqual(adapter.num_batches, 3)
        self.assertEqual(adapter.batch_size, 16)
        self.assertEqual(adapter.has_partial_batch, True)
        self.assertEqual(adapter.partial_batch_size, 2)

        if backend.backend() == "tensorflow":
            it = adapter.get_tf_dataset()
            if array_type == "tf_ragged":
                expected_class = tf.RaggedTensor
                xdim1 = None
                ydim1 = None
            elif array_type in ("tf_sparse", "jax_sparse", "scipy_sparse"):
                expected_class = tf.SparseTensor
            else:
                expected_class = tf.Tensor
        elif backend.backend() == "jax":
            it = adapter.get_jax_iterator()
            if array_type in ("tf_sparse", "jax_sparse", "scipy_sparse"):
                expected_class = jax_sparse.JAXSparse
            else:
                expected_class = np.ndarray
        elif backend.backend() == "torch":
            it = adapter.get_torch_dataloader()
            expected_class = torch.Tensor
        else:
            it = adapter.get_numpy_iterator()
            expected_class = np.ndarray

        x_order = []
        y_order = []
        for i, batch in enumerate(it):
            self.assertEqual(len(batch), 2)
            bx, by = batch
            self.assertIsInstance(bx, expected_class)
            self.assertIsInstance(by, expected_class)
            self.assertEqual(
                backend.standardize_dtype(bx.dtype), backend.floatx()
            )
            self.assertEqual(backend.standardize_dtype(by.dtype), "int32")
            if i < 2:
                self.assertEqual(bx.shape, (16, xdim1))
                self.assertEqual(by.shape, (16, ydim1))
            else:
                self.assertEqual(bx.shape, (2, xdim1))
                self.assertEqual(by.shape, (2, ydim1))

            if isinstance(bx, tf.SparseTensor):
                bx = tf.sparse.to_dense(bx)
                by = tf.sparse.to_dense(by)
            if isinstance(bx, jax_sparse.JAXSparse):
                bx = bx.todense()
                by = by.todense()
            x_batch_order = [float(bx[j, 0]) for j in range(bx.shape[0])]
            y_batch_order = [float(by[j, 0]) for j in range(by.shape[0])]
            x_order.extend(x_batch_order)
            y_order.extend(y_batch_order)

            if shuffle == "batch":
                self.assertAllClose(
                    sorted(x_batch_order),
                    list(range(i * 16, i * 16 + bx.shape[0])),
                )

        self.assertAllClose(x_order, y_order)
        if shuffle:
            self.assertNotAllClose(x_order, list(range(34)))
        else:
            self.assertAllClose(x_order, list(range(34)))