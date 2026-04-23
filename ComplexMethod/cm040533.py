def test_bincount(self, sparse_input, sparse_arg):
        if (sparse_input or sparse_arg) and not backend.SUPPORTS_SPARSE_TENSORS:
            pytest.skip("Backend does not support sparse tensors")

        x = x_np = np.array([1, 1, 2, 3, 2, 4, 4, 6])
        weights = weights_np = np.array([0, 0, 3, 2, 1, 1, 4, 2])
        if sparse_input:
            indices = np.array([[1], [3], [5], [7], [9], [11], [13], [15]])

            if backend.backend() == "tensorflow":
                import tensorflow as tf

                x = tf.SparseTensor(indices, x, (16,))
                weights = tf.SparseTensor(indices, weights, (16,))
            elif backend.backend() == "jax":
                from jax.experimental import sparse as jax_sparse

                x = jax_sparse.BCOO((x, indices), shape=(16,))
                weights = jax_sparse.BCOO((weights, indices), shape=(16,))

        minlength = 3
        output = knp.bincount(
            x, weights=weights, minlength=minlength, sparse=sparse_arg
        )
        self.assertAllClose(
            output, np.bincount(x_np, weights=weights_np, minlength=minlength)
        )
        self.assertSparse(output, sparse_input or sparse_arg)
        output = knp.Bincount(
            weights=weights, minlength=minlength, sparse=sparse_arg
        )(x)
        self.assertAllClose(
            output, np.bincount(x_np, weights=weights_np, minlength=minlength)
        )
        self.assertSparse(output, sparse_input or sparse_arg)

        x = knp.expand_dims(x, 0)
        weights = knp.expand_dims(weights, 0)

        expected_output = np.array([[0, 0, 4, 2, 5, 0, 2]])
        output = knp.bincount(
            x, weights=weights, minlength=minlength, sparse=sparse_arg
        )
        self.assertAllClose(output, expected_output)
        self.assertSparse(output, sparse_input or sparse_arg)
        output = knp.Bincount(
            weights=weights, minlength=minlength, sparse=sparse_arg
        )(x)
        self.assertAllClose(output, expected_output)
        self.assertSparse(output, sparse_input or sparse_arg)

        # test with weights=None
        expected_output = np.array([[0, 2, 2, 1, 2, 0, 1]])
        output = knp.Bincount(
            weights=None, minlength=minlength, sparse=sparse_arg
        )(x)
        self.assertAllClose(output, expected_output)
        self.assertSparse(output, sparse_input or sparse_arg)