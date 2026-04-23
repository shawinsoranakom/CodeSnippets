def _avg_pool_input_wrangler(
    args: list[Any], kwargs: dict[str, Any]
) -> tuple[list[Any], dict[str, Any]]:
    if "dim" not in kwargs:
        if len(args) > 6:
            kwargs["divisor_override"] = args.pop(6)
        if len(args) > 5:
            kwargs["count_include_pad"] = args.pop(5)
        if len(args) > 4:
            kwargs["ceil_mode"] = args.pop(4)
        if len(args) > 3:
            padding = args.pop(3)
            if isinstance(padding, np.ndarray):
                # Cannot using list(padding) here, because the element will be numpy.int64 instead of int
                padding = padding.tolist()
            kwargs["padding"] = padding
        if len(args) > 2:
            stride = args.pop(2)
            if isinstance(stride, np.ndarray):
                stride = stride.tolist()
            kwargs["stride"] = stride
        kernel_size = args.pop(1)
        if isinstance(kernel_size, np.ndarray):
            kernel_size = kernel_size.tolist()
        kwargs["kernel_size"] = kernel_size
    return args, kwargs