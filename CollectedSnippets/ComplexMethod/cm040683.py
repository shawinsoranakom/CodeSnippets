def make_array(self, array_type, shape, dtype):
        x = np.array([[i] * shape[1] for i in range(shape[0])], dtype=dtype)
        if array_type == "np":
            return x
        elif array_type == "tf":
            return tf.constant(x)
        elif array_type == "tf_ragged":
            return tf.RaggedTensor.from_tensor(x)
        elif array_type == "tf_sparse":
            return tf.sparse.from_dense(x)
        elif array_type == "jax":
            return jax.numpy.array(x)
        elif array_type == "jax_sparse":
            return jax_sparse.BCOO.fromdense(x)
        elif array_type == "torch":
            return torch.as_tensor(x)
        elif array_type == "pandas_data_frame":
            return pandas.DataFrame(x)
        elif array_type == "pandas_series":
            return pandas.Series(x[:, 0])
        elif array_type == "scipy_sparse":
            return scipy.sparse.coo_matrix(x)