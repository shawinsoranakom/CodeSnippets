def cal_conv_generated_kernel_number(mod, input, dtype, dim=4, device="cpu"):
    # this function is to decide how many kernels are generated
    # while testing conv2d/3d/deconv2d
    # the assumption is:
    #   (1) There will be a to_dtype kernel for input for lp
    #   (2) inductor always use channel_last format, there will
    #       be a to_channel_last format for input
    #   (3) to_dtype and to_channel_last for input can be fused
    #   (4) inductor always get channel last format from mkldnn_conv_pointwise(binary),
    #       and force the output to have same stride with eager.
    #       So there will be a to_contiguous for output if eager output is contiguouse
    mod = copy.deepcopy(mod)
    mod = mod.to(device=device)
    input = input.clone()
    input = input.to(device)

    if dtype == torch.float32:
        maybe_autocast = contextlib.nullcontext()
    else:
        maybe_autocast = torch.amp.autocast(device_type=device, dtype=dtype)
    with torch.no_grad(), maybe_autocast:
        output = mod(input)
    input_kernel, output_kernel = 0, 0
    if (
        input.is_contiguous(memory_format=torch.contiguous_format)
        or dtype != torch.float32
        or (TEST_ACL and dim == 4)
    ):
        input_kernel = 1
    if output.is_contiguous(memory_format=torch.contiguous_format) or (
        TEST_ACL and (dtype == torch.bfloat16 or dtype == torch.half)
    ):
        output_kernel = 1

    return input_kernel + output_kernel