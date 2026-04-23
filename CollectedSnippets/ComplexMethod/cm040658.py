def encode_categorical_inputs(
    inputs,
    output_mode,
    depth,
    dtype,
    sparse=False,
    count_weights=None,
    backend_module=None,
):
    """Encodes categorical inputs according to output_mode.

    Args:
        inputs: the inputs to encode.
        output_mode: one of `"int"`, `"one_hot"`, `"multi_hot"`, or `"count"`.
        depth: number of classes, this will be the last dimension of the output.
        dtype: the dtype of the output, unless `count_weights` is not `None`.
        sparse: whether the output should be sparse for backends supporting it.
        count_weights: weights to apply if `output_mode` is `"count"`.
        backend_module: the backend to use instead of the current one.

    Returns: the encoded inputs.
    """
    backend_module = backend_module or backend

    if output_mode == "int":
        return backend_module.cast(inputs, dtype=dtype)

    rank_of_inputs = len(backend_module.shape(inputs))

    # In all cases, we should uprank scalar input to a single sample.
    if rank_of_inputs == 0:
        inputs = backend_module.numpy.expand_dims(inputs, -1)
        rank_of_inputs = 1

    if (
        backend_module.__name__.endswith("tensorflow")
        and rank_of_inputs <= 2
        and output_mode in ("multi_hot", "count")
    ):
        # TF only fastpath. Uses bincount; faster. Doesn't work for rank 3+.
        try:
            return tf_utils.tf_encode_categorical_inputs(
                inputs,
                output_mode,
                depth,
                dtype=dtype,
                sparse=sparse,
                count_weights=count_weights,
            )
        except ValueError:
            pass

    if output_mode == "multi_hot":
        return backend_module.nn.multi_hot(
            inputs, depth, dtype=dtype, sparse=sparse
        )
    elif output_mode == "one_hot":
        input_shape = backend_module.core.shape(inputs)
        # Shrink the last dimension if the shape is (..., 1).
        if (
            input_shape is not None
            and len(input_shape) > 1
            and input_shape[-1] == 1
        ):
            newshape = tuple(input_shape[:-1])
            inputs = backend_module.numpy.reshape(inputs, newshape)
        return backend_module.nn.one_hot(
            inputs, depth, dtype=dtype, sparse=sparse
        )
    elif output_mode == "count":
        # We don't use `ops.bincount` because its output has a dynamic shape
        # (last dimension is the highest value of `inputs`). We implement a
        # narrower use case where `minlength` and `maxlength` (not supported by
        # `ops.bincount`) are the same and static value: `depth`. We also don't
        # need to support indices that are negative or greater than `depth`.
        reduction_axis = 1 if len(inputs.shape) > 1 else 0

        if count_weights is not None:
            dtype = count_weights.dtype
        one_hot_encoding = backend_module.nn.one_hot(
            inputs, depth, dtype=dtype, sparse=sparse
        )
        if count_weights is not None:
            count_weights = backend_module.numpy.expand_dims(count_weights, -1)
            one_hot_encoding = one_hot_encoding * count_weights

        outputs = backend_module.numpy.sum(
            one_hot_encoding,
            axis=reduction_axis,
        )
        return outputs