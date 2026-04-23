def symbolic_fn(g, input, output_size):
        # _adaptive_pool is supported for cases where output_size is 1 for all dimensions,
        # by executing a GlobalPool.
        # It is also supported for cases where the output size is a factor of the input size.
        # For these cases the stride and kernel size are uniform along all the indices of
        # the same dimension, which makes it possible to export it to ONNX.
        # for MaxPool, GlobalMaxPool does not return indices,
        # so we try using max_poolxd_with_indices, and if it is not possible
        # (input is not a complete tensor or output size not factor of input size)
        # then we call GlobalAveragePool and return None for the indices
        output_size_value = output_size
        try:
            output_size = symbolic_helper._parse_arg(output_size, "is")
        except Exception:
            # FIXME(justinchuby): Avoid catching Exception.
            # Catch a more specific exception instead.
            return symbolic_helper._onnx_unsupported(
                "adaptive pooling, since output_size is not constant.", input
            )
        if output_size == [1] * len(output_size) and type == "AveragePool":
            return g.op("GlobalAveragePool", input)
        sizes = symbolic_helper._get_tensor_sizes(input)
        try:
            dim = sizes[2:]
        except Exception:
            # FIXME(justinchuby): Avoid catching Exception.
            # Catch a more specific exception instead.
            dim = None
        if dim is None or any(i is None for i in dim):
            if output_size == [1] * len(output_size):
                return g.op("GlobalMaxPool", input), None
            return symbolic_helper._unimplemented(
                name, "input size not accessible", input
            )
        # verify if output size % input size = 0 for all dim
        mod = [dim[i] % output_size[i] for i in range(len(dim))]
        if mod != [0] * len(mod):
            if output_size == [1] * len(output_size):
                return g.op("GlobalMaxPool", input), None
            return symbolic_helper._unimplemented(
                name, "output size that are not factor of input size", output_size_value
            )
        k = [int(dim[i] / output_size[i]) for i in range(len(dim))]
        # call max_poolxd_with_indices to get indices in the output
        if type == "MaxPool":
            # pyrefly: ignore [not-callable]
            return fn(g, input, k, k, (0,) * len(dim), (1,) * len(dim), False)
        output = g.op(type, input, kernel_shape_i=tuple_fn(k), strides_i=tuple_fn(k))
        return output