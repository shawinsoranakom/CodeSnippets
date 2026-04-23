def _calculate_flops(event: dict[str, Any]) -> int:
    """
    This function has to parse the kernel name, which is error prone. There doesn't seem to be another solution that
    will support all the different backends that can generate kernels, so make sure to update this function when new
    ops and backends are desired.
    """
    name = event["name"]
    if "kernel_flop" in event["args"] and event["args"]["kernel_flop"] != 0:
        return event["args"]["kernel_flop"]
    op_name = _parse_kernel_name(name)
    if op_name is None:
        return 0

    op_obj = getattr(torch.ops.aten, op_name, None)
    if op_obj is None or op_obj not in flop_registry:
        return 0

    flop_function = flop_registry[op_obj]

    if "Input Dims" not in event["args"] or "Concrete Inputs" not in event["args"]:
        return 0
    input_shapes = event["args"]["Input Dims"]
    concrete = event["args"]["Concrete Inputs"]
    if op_name in adapters_map:
        try:
            args, kwargs = adapters_map[op_name](input_shapes, concrete)
        except ParseException as e:
            msg = f"Failed to parse {op_name} with {e}"
            log.warning(msg)
            return 0
    else:
        try:
            args, kwargs = default_adapter(input_shapes, concrete)
        except ParseException as e:
            msg = f"Failed to parse {op_name} with {e}"
            log.warning(msg)
            return 0
    return flop_function(*args, **kwargs)