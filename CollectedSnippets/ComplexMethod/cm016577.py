def cast_bias_weight_with_vbar(s, dtype, device, bias_dtype, non_blocking, compute_dtype, want_requant):

    #vbar doesn't support CPU weights, but some custom nodes have weird paths
    #that might switch the layer to the CPU and expect it to work. We have to take
    #a clone conservatively as we are mmapped and some SFT files are packed misaligned
    #If you are a custom node author reading this, please move your layer to the GPU
    #or declare your ModelPatcher as CPU in the first place.
    if comfy.model_management.is_device_cpu(device):
        weight = s.weight.to(dtype=dtype, copy=True)
        if isinstance(weight, QuantizedTensor):
            weight = weight.dequantize()
        bias = None
        if s.bias is not None:
            bias = s.bias.to(dtype=bias_dtype, copy=True)
        return weight, bias, (None, None, None)

    offload_stream = None
    xfer_dest = None

    signature = comfy_aimdo.model_vbar.vbar_fault(s._v)
    resident = comfy_aimdo.model_vbar.vbar_signature_compare(signature, s._v_signature)
    if signature is not None:
        if resident:
            weight = s._v_weight
            bias = s._v_bias
        else:
            xfer_dest = comfy_aimdo.torch.aimdo_to_tensor(s._v, device)

    if not resident:
        cast_geometry = comfy.memory_management.tensors_to_geometries([ s.weight, s.bias ])
        cast_dest = None

        xfer_source = [ s.weight, s.bias ]

        pin = comfy.pinned_memory.get_pin(s)
        if pin is not None:
            xfer_source = [ pin ]

        for data, geometry in zip([ s.weight, s.bias ], cast_geometry):
            if data is None:
                continue
            if data.dtype != geometry.dtype:
                cast_dest = xfer_dest
                if cast_dest is None:
                    cast_dest = torch.empty((comfy.memory_management.vram_aligned_size(cast_geometry),), dtype=torch.uint8, device=device)
                xfer_dest = None
                break

        dest_size = comfy.memory_management.vram_aligned_size(xfer_source)
        offload_stream = comfy.model_management.get_offload_stream(device)
        if xfer_dest is None and offload_stream is not None:
                xfer_dest = comfy.model_management.get_cast_buffer(offload_stream, device, dest_size, s)
                if xfer_dest is None:
                    offload_stream = comfy.model_management.get_offload_stream(device)
                    xfer_dest = comfy.model_management.get_cast_buffer(offload_stream, device, dest_size, s)
        if xfer_dest is None:
            xfer_dest = torch.empty((dest_size,), dtype=torch.uint8, device=device)
            offload_stream = None

        if signature is None and pin is None:
            comfy.pinned_memory.pin_memory(s)
            pin = comfy.pinned_memory.get_pin(s)
        else:
            pin = None

        if pin is not None:
            comfy.model_management.cast_to_gathered(xfer_source, pin)
            xfer_source = [ pin ]
        #send it over
        comfy.model_management.cast_to_gathered(xfer_source, xfer_dest, non_blocking=non_blocking, stream=offload_stream)
        comfy.model_management.sync_stream(device, offload_stream)

        if cast_dest is not None:
            for pre_cast, post_cast in zip(comfy.memory_management.interpret_gathered_like([s.weight, s.bias ], xfer_dest),
                                           comfy.memory_management.interpret_gathered_like(cast_geometry, cast_dest)):
                if post_cast is not None:
                    post_cast.copy_(pre_cast)
            xfer_dest = cast_dest

        params = comfy.memory_management.interpret_gathered_like(cast_geometry, xfer_dest)
        weight = params[0]
        bias = params[1]
        if signature is not None:
            s._v_weight = weight
            s._v_bias = bias
        s._v_signature=signature

    def post_cast(s, param_key, x, dtype, resident, update_weight):
        lowvram_fn = getattr(s, param_key + "_lowvram_function", None)
        fns = getattr(s, param_key + "_function", [])

        orig = x

        def to_dequant(tensor, dtype):
            tensor = tensor.to(dtype=dtype)
            if isinstance(tensor, QuantizedTensor):
                tensor = tensor.dequantize()
            return tensor

        if orig.dtype != dtype or len(fns) > 0:
            x = to_dequant(x, dtype)
        if not resident and lowvram_fn is not None:
            x = to_dequant(x, dtype if compute_dtype is None else compute_dtype)
            x = lowvram_fn(x)
            if (want_requant and len(fns) == 0 or update_weight):
                seed = comfy.utils.string_to_seed(s.seed_key)
                if isinstance(orig, QuantizedTensor):
                    y = QuantizedTensor.from_float(x, s.layout_type, scale="recalculate", stochastic_rounding=seed)
                else:
                    y = comfy.float.stochastic_rounding(x, orig.dtype, seed=seed)
            if want_requant and len(fns) == 0:
                x = y
            if update_weight:
                orig.copy_(y)
        for f in fns:
            x = f(x)
        return x

    update_weight = signature is not None

    weight = post_cast(s, "weight", weight, dtype, resident, update_weight)
    if s.bias is not None:
        bias = post_cast(s, "bias", bias, bias_dtype, resident, update_weight)

    #FIXME: weird offload return protocol
    return weight, bias, (offload_stream, device if signature is not None else None, None)