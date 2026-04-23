def uncast_bias_weight(s, weight, bias, offload_stream):
    if offload_stream is None:
        return
    os, weight_a, bias_a = offload_stream
    device=None
    #FIXME: This is really bad RTTI
    if weight_a is not None and not isinstance(weight_a, torch.Tensor):
        comfy_aimdo.model_vbar.vbar_unpin(s._v)
        device = weight_a
    if os is None:
        return
    if device is None:
        if weight_a is not None:
            device = weight_a.device
        else:
            if bias_a is None:
                return
            device = bias_a.device
    os.wait_stream(comfy.model_management.current_stream(device))