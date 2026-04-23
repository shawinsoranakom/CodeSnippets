def symbolic_fn(g, input, kernel_size, stride, padding, dilation, ceil_mode):
        if set(tuple_fn(dilation)) != {1}:
            return symbolic_helper._unimplemented(name, "dilation", input)
        if not stride:
            stride = kernel_size
        padding = tuple(tuple_fn(padding))
        if ceil_mode:
            padding_ceil = get_pool_ceil_padding(input, kernel_size, stride, padding)
            padding = padding + tuple(a + b for (a, b) in zip(padding_ceil, padding))
        else:
            padding = padding * 2
        kwargs = {
            "kernel_shape_i": tuple_fn(kernel_size),
            "pads_i": padding,
            "strides_i": tuple_fn(stride),
        }
        # easy but hacky way to get flattened indices values
        # to be used to convert the indices values to non-flattened.
        # In ONNX the indices are computed as a flatten 1-D tensor,
        # so the values in indices are in [0, N x C x D1 x ... x Dn).
        # To convert the indices to the same format used by Pytorch,
        # we first execute a maxpool with a kernel and stride of 1 on the same input.
        # This will result in a tensor of indices in which each index will have it's own value.
        # Using this tensor as a reference, we extract the first index of each axis and subtract
        # it from each index of this axis in the indices to convert.
        # This step will result in a tensor were each dimension has values of indices within
        # the dimension it is in.
        # For more information :
        # https://github.com/pytorch/pytorch/pull/16455#issuecomment-460776407
        if return_indices:
            r, indices = g.op("MaxPool", input, outputs=2, **kwargs)
            _, flattened_indices = g.op(
                "MaxPool",
                input,
                outputs=2,
                kernel_shape_i=[1 for _ in range(ndims)],
                strides_i=[1 for _ in range(ndims)],
            )
            # convert indices to have non-flattened indices values
            s = symbolic_helper._slice_helper(
                g,
                flattened_indices,
                axes=[2 + i for i in range(ndims)],
                starts=list(tuple_fn(0)),
                ends=list(tuple_fn(1)),
            )
            indices = sub(g, indices, s)
            return r, indices
        else:
            r = g.op("MaxPool", input, outputs=1, **kwargs)
            return r