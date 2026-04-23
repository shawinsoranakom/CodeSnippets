def _check_input_shape_and_type(self, inputs):
        first_shape = tuple(inputs[0].shape)
        rank = len(first_shape)
        if rank > 2 or (rank == 2 and first_shape[-1] != 1):
            raise ValueError(
                "All `HashedCrossing` inputs should have shape `()`, "
                "`(batch_size)` or `(batch_size, 1)`. "
                f"Received: inputs={inputs}"
            )
        if not all(tuple(x.shape) == first_shape for x in inputs[1:]):
            raise ValueError(
                "All `HashedCrossing` inputs should have equal shape. "
                f"Received: inputs={inputs}"
            )
        if any(
            isinstance(x, (tf.RaggedTensor, tf.SparseTensor)) for x in inputs
        ):
            raise ValueError(
                "All `HashedCrossing` inputs should be dense tensors. "
                f"Received: inputs={inputs}"
            )
        if not all(
            tf.as_dtype(x.dtype).is_integer or x.dtype == tf.string
            for x in inputs
        ):
            raise ValueError(
                "All `HashedCrossing` inputs should have an integer or "
                f"string dtype. Received: inputs={inputs}"
            )