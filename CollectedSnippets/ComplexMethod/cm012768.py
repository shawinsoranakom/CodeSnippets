def _estimate_gb(event: dict[str, Any]) -> float:
    """
    Our best effort to estimate the gb, should be refactored soon with MemoryCounter.
    """
    name = event["name"]
    if "kernel_num_gb" in event["args"] and event["args"]["kernel_num_gb"] != 0:
        return event["args"]["kernel_num_gb"]
    if "Input type" not in event["args"] or "Input Dims" not in event["args"]:
        return 0
    op_name = _parse_kernel_name(name)
    if op_name is None:
        return _default_estimate_gb(event)

    op_obj = getattr(torch.ops.aten, op_name, None)
    if op_obj is None:
        return _default_estimate_gb(event)

    if "Input Dims" not in event["args"] or "Concrete Inputs" not in event["args"]:
        return _default_estimate_gb(event)
    input_shapes = event["args"]["Input Dims"]

    # NOTE these will be refactored into a similar object to FlopCounter soon
    def mm_formula(M: int, N: int, K: int, size: int) -> int:
        return 2 * (M * K + N * K + M * N) * size

    if op_name == "addmm":
        add_in_size = math.prod(pytree.tree_flatten(input_shapes[0])[0])
        add_type_size = _get_size_from_string(event["args"]["Input type"][0])
        M = input_shapes[1][0]
        N = input_shapes[1][1]
        assert input_shapes[1][1] == input_shapes[2][0]
        K = input_shapes[2][1]
        mul_type_size = _get_size_from_string(event["args"]["Input type"][1])
        return (mm_formula(M, N, K, mul_type_size) + add_in_size * add_type_size) / 1e9
    elif op_name == "mm":
        M = input_shapes[0][0]
        N = input_shapes[0][1]
        assert input_shapes[0][1] == input_shapes[1][0]
        K = input_shapes[1][1]
        type_size = _get_size_from_string(event["args"]["Input type"][0])
        return mm_formula(M, N, K, type_size) / 1e9
    elif op_name == "baddbmm":
        add_in_size = math.prod(pytree.tree_flatten(input_shapes[0])[0])
        add_type_size = _get_size_from_string(event["args"]["Input type"][0])
        B = input_shapes[0][0]
        M = input_shapes[1][1]
        N = input_shapes[1][2]
        K = input_shapes[2][2]
        mul_type_size = _get_size_from_string(event["args"]["Input type"][1])
        return (
            B * mm_formula(M, N, K, mul_type_size) + add_in_size * add_type_size
        ) / 1e9
    elif op_name == "bmm":
        add_in_size = math.prod(pytree.tree_flatten(input_shapes[0])[0])
        add_type_size = _get_size_from_string(event["args"]["Input type"][0])
        B = input_shapes[0][0]
        M = input_shapes[0][1]
        N = input_shapes[0][2]
        K = input_shapes[1][2]
        mul_type_size = _get_size_from_string(event["args"]["Input type"][1])
        return (
            B * mm_formula(M, N, K, mul_type_size) + add_in_size * add_type_size
        ) / 1e9
    elif op_name in [
        "convolution",
        "_convolution",
        "cudnn_convolution",
        "_slow_conv2d_forward",
    ]:
        concrete = event["args"]["Concrete Inputs"]

        def conv_out_dim(x: int, kernel: int, stride: int) -> int:
            return (x - kernel) // stride + 1

        stride = parse_list(
            concrete[3] if op_name != "_slow_conv2d_forward" else concrete[4]
        )
        inp = input_shapes[0]
        w = input_shapes[1]
        out_x_y = [conv_out_dim(*args) for args in zip(inp[2:], w[2:], stride)]
        out = [inp[0], w[0]] + out_x_y
        # each output element reads in * w * w chunk
        input_reads = out[0] * out[1] * out[2] * out[3] * inp[1] * w[2] * w[3]
        # Assume weights are in cache, so only read once
        weight_reads = w[0] * w[1] * w[2] * w[3]
        return (input_reads + weight_reads) / 1e9

    return _default_estimate_gb(event)