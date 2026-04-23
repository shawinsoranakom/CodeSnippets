def get_pool_ceil_padding(input, kernel_size, stride, padding):
    # TODO(justinchuby): Looks like this op is deprecated in torch
    sizes = symbolic_helper._get_tensor_sizes(input)
    dim = sizes[-len(padding) :] if sizes is not None else None
    if dim is None or any(i is None for i in dim):
        return symbolic_helper._unimplemented(
            "get_pool_ceil_padding", "input size not accessible", input
        )
    ceiled_output_dim = [
        math.ceil((dim[i] + 2 * padding[i] - kernel_size[i]) / float(stride[i])) + 1
        for i in range(len(padding))
    ]
    # ensure last pooling starts inside
    ceiled_output_dim = [
        (
            ceiled_output_dim[i] - 1
            if (((ceiled_output_dim[i] - 1) * stride[i]) >= (dim[i] + padding[i]))
            else ceiled_output_dim[i]
        )
        for i in range(len(ceiled_output_dim))
    ]
    padding_ceil = [
        (
            0
            if (stride[i] == 1)
            else (
                kernel_size[i]
                - (
                    dim[i]
                    + 2 * padding[i]
                    - ((ceiled_output_dim[i] - 1) * stride[i] + 1)
                )
            )
        )
        for i in range(len(padding))
    ]
    # ensure padding is not > kernel_size
    padding_ceil = [
        (
            (
                int(padding_ceil[i])
                if padding_ceil[i] < kernel_size[i] - 1
                else int(kernel_size[i] - 1)
            )
            if ((padding_ceil[i] + 2 * padding[i]) >= (kernel_size[i]))
            else int(padding_ceil[i])
        )
        for i in range(len(padding_ceil))
    ]
    return padding_ceil