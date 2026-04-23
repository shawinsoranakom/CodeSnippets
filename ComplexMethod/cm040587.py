def create_eager_tensors(input_shape, dtype, sparse, ragged):
    from keras.src.backend import random

    if set(tree.flatten(dtype)).difference(
        [
            "float16",
            "float32",
            "float64",
            "int8",
            "uint8",
            "int16",
            "uint16",
            "int32",
            "uint32",
            "int64",
            "uint64",
        ]
    ):
        raise ValueError(
            "dtype must be a standard float or int dtype. "
            f"Received: dtype={dtype}"
        )

    if sparse:
        if backend.backend() == "tensorflow":
            import tensorflow as tf

            def create_fn(shape, dt):
                rng = np.random.default_rng(0)
                x = (4 * rng.standard_normal(shape)).astype(dt)
                x = np.multiply(x, rng.random(shape) < 0.7)
                return tf.sparse.from_dense(x)

        elif backend.backend() == "jax":
            import jax.experimental.sparse as jax_sparse

            def create_fn(shape, dt):
                rng = np.random.default_rng(0)
                x = (4 * rng.standard_normal(shape)).astype(dt)
                x = np.multiply(x, rng.random(shape) < 0.7)
                return jax_sparse.BCOO.fromdense(x, n_batch=1)

        else:
            raise ValueError(
                f"Sparse is unsupported with backend {backend.backend()}"
            )

    elif ragged:
        if backend.backend() == "tensorflow":
            import tensorflow as tf

            def create_fn(shape, dt):
                rng = np.random.default_rng(0)
                x = (4 * rng.standard_normal(shape)).astype(dt)
                x = np.multiply(x, rng.random(shape) < 0.7)
                return tf.RaggedTensor.from_tensor(x, padding=0)

        else:
            raise ValueError(
                f"Ragged is unsupported with backend {backend.backend()}"
            )

    else:

        def create_fn(shape, dt):
            return ops.cast(
                random.uniform(shape, dtype="float32") * 3, dtype=dt
            )

    if isinstance(input_shape, dict):
        return {
            utils.removesuffix(k, "_shape"): create_fn(v, dtype[k])
            for k, v in input_shape.items()
        }
    return map_shape_dtype_structure(create_fn, input_shape, dtype)