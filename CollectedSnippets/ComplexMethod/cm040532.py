def test_matmul_sparse(self, dtype, x_shape, y_shape, x_sparse, y_sparse):
        if backend.backend() == "tensorflow":
            import tensorflow as tf

            if x_sparse and y_sparse and dtype in ("float16", "int32"):
                pytest.skip(
                    f"Sparse sparse matmul unsupported for {dtype}"
                    " with TensorFlow backend"
                )

            dense_to_sparse = tf.sparse.from_dense
        elif backend.backend() == "jax":
            import jax.experimental.sparse as jax_sparse

            if (
                x_sparse
                and y_sparse
                and len(x_shape) == 4
                and dtype in ("float32", "float64", "int32")
                and testing.jax_uses_tpu()
            ):
                pytest.skip(
                    "Sparse sparse matmul crashes for rank 4 and float32 with "
                    "JAX on some TPUs"
                )

            dense_to_sparse = functools.partial(
                jax_sparse.BCOO.fromdense, n_batch=len(x_shape) - 2
            )

        rng = np.random.default_rng(0)

        x = x_np = (4 * rng.standard_normal(x_shape)).astype(dtype)
        if x_sparse:
            x_np = np.multiply(x_np, rng.random(x_shape) < 0.7)
            x = dense_to_sparse(x_np)

        y = y_np = (4 * rng.standard_normal(y_shape)).astype(dtype)
        if y_sparse:
            y_np = np.multiply(y_np, rng.random(y_shape) < 0.7)
            y = dense_to_sparse(y_np)

        atol = 0.1 if dtype == "float16" else 1e-4
        tpu_atol = 1 if dtype == "float16" else 1e-1
        self.assertAllClose(
            knp.matmul(x, y),
            np.matmul(x_np, y_np),
            atol=atol,
            tpu_atol=tpu_atol,
            tpu_rtol=tpu_atol,
        )
        self.assertSparse(knp.matmul(x, y), x_sparse and y_sparse)