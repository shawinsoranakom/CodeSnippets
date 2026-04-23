def get_single_tensor_spec(*tensors):
        x = tensors[0]
        if not hasattr(x, "shape"):
            # Try to convert to a numpy array.
            x = np.array(x)
        rank = len(x.shape)
        if rank < 1:
            raise ValueError(
                "When passing a dataset to a Keras model, the arrays must "
                f"be at least rank 1. Received: {x} of rank {len(x.shape)}."
            )
        for t in tensors:
            if len(t.shape) != rank:
                raise ValueError(
                    "When passing a dataset to a Keras model, the "
                    "corresponding arrays in each batch must have the same "
                    f"rank. Received: {x} and {t}"
                )
        shape = []
        # Merge shapes: go through each dimension one by one and keep the
        # common values
        for dims in zip(*[list(x.shape) for x in tensors]):
            dims_set = set(dims)
            shape.append(dims_set.pop() if len(dims_set) == 1 else None)

        dtype = backend.standardize_dtype(x.dtype)
        if is_tensorflow_ragged(x):
            return backend.KerasTensor(
                shape=shape,
                dtype=dtype,
                ragged=True,
                ragged_rank=x.ragged_rank,
                row_splits_dtype=x.row_splits.dtype,
            )
        if is_tensorflow_sparse(x) or is_scipy_sparse(x) or is_jax_sparse(x):
            return backend.KerasTensor(shape=shape, dtype=dtype, sparse=True)
        else:
            return backend.KerasTensor(shape=shape, dtype=dtype)