def wrapped(*args, **kwargs):
        excluded_func, args, kwargs = _vectorize_apply_excluded(
            pyfunc, excluded, args, kwargs
        )

        if signature is not None:
            input_core_dims, output_core_dims = (
                _vectorize_parse_gufunc_signature(signature)
            )
        else:
            input_core_dims = [()] * len(args)
            output_core_dims = None

        none_args = {i for i, arg in enumerate(args) if arg is None}
        if any(none_args):
            if any(input_core_dims[i] != () for i in none_args):
                raise ValueError(
                    f"Cannot pass None at locations {none_args} "
                    f"with signature={signature}"
                )
            excluded_func, args, _ = _vectorize_apply_excluded(
                excluded_func, none_args, args, {}
            )
            input_core_dims = [
                dim
                for i, dim in enumerate(input_core_dims)
                if i not in none_args
            ]

        args = tuple(map(ops.convert_to_tensor, args))

        broadcast_shape, dim_sizes = _vectorize_parse_input_dimensions(
            args, input_core_dims
        )
        checked_func = _vectorize_check_output_dims(
            excluded_func, dim_sizes, output_core_dims
        )
        squeezed_args = []
        rev_filled_shapes = []
        for arg, core_dims in zip(args, input_core_dims):
            noncore_shape = arg.shape[: arg.ndim - len(core_dims)]

            pad_ndim = len(broadcast_shape) - len(noncore_shape)
            filled_shape = pad_ndim * (1,) + noncore_shape
            rev_filled_shapes.append(filled_shape[::-1])

            squeeze_indices = tuple(
                i for i, size in enumerate(noncore_shape) if size == 1
            )
            squeezed_arg = ops.squeeze(arg, axis=squeeze_indices)
            squeezed_args.append(squeezed_arg)

        vectorized_func = checked_func
        dims_to_expand = []
        for negdim, axis_sizes in enumerate(zip(*rev_filled_shapes)):
            in_axes = tuple(None if size == 1 else 0 for size in axis_sizes)
            if all(axis is None for axis in in_axes):
                dims_to_expand.append(len(broadcast_shape) - 1 - negdim)
            else:
                vectorized_func = vmap_fn(vectorized_func, in_axes)
        result = vectorized_func(*squeezed_args)

        if not dims_to_expand:
            return result
        elif isinstance(result, tuple):
            return tuple(
                ops.expand_dims(r, axis=dims_to_expand) for r in result
            )
        else:
            return ops.expand_dims(result, axis=dims_to_expand)