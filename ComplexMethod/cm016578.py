def cast_bias_weight(s, input=None, dtype=None, device=None, bias_dtype=None, offloadable=False, compute_dtype=None, want_requant=False):
    # NOTE: offloadable=False is a a legacy and if you are a custom node author reading this please pass
    # offloadable=True and call uncast_bias_weight() after your last usage of the weight/bias. This
    # will add async-offload support to your cast and improve performance.
    if input is not None:
        if dtype is None:
            if isinstance(input, QuantizedTensor):
                dtype = input.params.orig_dtype
            else:
                dtype = input.dtype
        if bias_dtype is None:
            bias_dtype = dtype
        if device is None:
            device = input.device

    non_blocking = comfy.model_management.device_supports_non_blocking(device)

    if hasattr(s, "_v"):
        return cast_bias_weight_with_vbar(s, dtype, device, bias_dtype, non_blocking, compute_dtype, want_requant)

    if offloadable and (device != s.weight.device or
                        (s.bias is not None and device != s.bias.device)):
        offload_stream = comfy.model_management.get_offload_stream(device)
    else:
        offload_stream = None

    bias = None
    weight = None

    if offload_stream is not None and not args.cuda_malloc:
        cast_buffer_size = comfy.memory_management.vram_aligned_size([ s.weight, s.bias ])
        cast_buffer = comfy.model_management.get_cast_buffer(offload_stream, device, cast_buffer_size, s)
        #The streams can be uneven in buffer capability and reject us. Retry to get the other stream
        if cast_buffer is None:
            offload_stream = comfy.model_management.get_offload_stream(device)
            cast_buffer = comfy.model_management.get_cast_buffer(offload_stream, device, cast_buffer_size, s)
        params = comfy.memory_management.interpret_gathered_like([ s.weight, s.bias ], cast_buffer)
        weight = params[0]
        bias = params[1]

    weight_has_function = len(s.weight_function) > 0
    bias_has_function = len(s.bias_function) > 0

    weight = comfy.model_management.cast_to(s.weight, None, device, non_blocking=non_blocking, copy=weight_has_function, stream=offload_stream, r=weight)

    if s.bias is not None:
        bias = comfy.model_management.cast_to(s.bias, None, device, non_blocking=non_blocking, copy=bias_has_function, stream=offload_stream, r=bias)

    comfy.model_management.sync_stream(device, offload_stream)

    bias_a = bias
    weight_a = weight

    if s.bias is not None:
        bias = bias.to(dtype=bias_dtype)
        for f in s.bias_function:
            bias = f(bias)

    if weight_has_function or weight.dtype != dtype:
        weight = weight.to(dtype=dtype)
        if isinstance(weight, QuantizedTensor):
            weight = weight.dequantize()
        for f in s.weight_function:
            weight = f(weight)

    if offloadable:
        return weight, bias, (offload_stream, weight_a, bias_a)
    else:
        #Legacy function signature
        return weight, bias