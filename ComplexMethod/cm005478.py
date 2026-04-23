def load_and_swizzle_mxfp4(module, param_name, param_value, target_device, triton_kernels_hub, **kwargs):
    """
    This transforms the weights obtained using `convert_gpt_oss.py` to load them into `Mxfp4GptOssExperts`.
    """
    PrecisionConfig, FlexCtx, InFlexData = (
        triton_kernels_hub.matmul_ogs.PrecisionConfig,
        triton_kernels_hub.matmul_ogs.FlexCtx,
        triton_kernels_hub.matmul_ogs.InFlexData,
    )
    from ..integrations.tensor_parallel import shard_and_distribute_module

    model = kwargs.get("model")
    empty_param = kwargs.get("empty_param")
    casting_dtype = kwargs.get("casting_dtype")
    to_contiguous = kwargs.get("to_contiguous")
    rank = kwargs.get("rank")
    device_mesh = kwargs.get("device_mesh")
    if "blocks" in param_name:
        proj = param_name.split(".")[-1].split("_blocks")[0]
    if "scales" in param_name:
        proj = param_name.split(".")[-1].split("_scales")[0]
    if device_mesh is not None:
        shard_and_distribute_module(
            model, param_value, empty_param, param_name, casting_dtype, to_contiguous, rank, device_mesh
        )
    else:
        setattr(module, param_name.rsplit(".", 1)[1], torch.nn.Parameter(param_value, requires_grad=False))
    blocks_attr = f"{proj}_blocks"
    scales_attr = f"{proj}_scales"
    blocks = getattr(module, blocks_attr)  # at this point values were loaded from ckpt
    scales = getattr(module, scales_attr)
    # Check if both blocks and scales both not on meta device
    if blocks.device.type != "meta" and scales.device.type != "meta":
        local_experts = blocks.size(0)
        if proj == "gate_up_proj":
            blocks = blocks.reshape(local_experts, module.intermediate_size * 2, -1)
        else:
            blocks = blocks.reshape(local_experts, -1, module.intermediate_size // 2)
        if (
            getattr(target_device, "type", target_device) == "cpu"
            and hasattr(torch, "accelerator")
            and torch.accelerator.current_accelerator() is not None
        ):
            target_device = torch.accelerator.current_accelerator().type
        blocks = blocks.to(target_device).contiguous()
        scales = scales.to(target_device).contiguous()
        with on_device(target_device):
            triton_weight_tensor, weight_scale = swizzle_mxfp4(
                blocks.transpose(-2, -1), scales.transpose(-2, -1), triton_kernels_hub
            )

        # need to overwrite the shapes for the kernels
        if proj == "gate_up_proj":
            triton_weight_tensor.shape = torch.Size([local_experts, module.hidden_size, module.intermediate_size * 2])
        else:
            triton_weight_tensor.shape = torch.Size([local_experts, module.intermediate_size, module.hidden_size])

        # triton_weight_tensor is what needs to be passed in oai kernels. It stores the data, the shapes and any more objects. It is like a subtensor
        setattr(module, proj, triton_weight_tensor)
        setattr(
            module,
            f"{proj}_precision_config",
            PrecisionConfig(weight_scale=weight_scale, flex_ctx=FlexCtx(rhs_data=InFlexData())),
        )

        # delete blocks and scales
        delattr(module, scales_attr)
        delattr(module, blocks_attr)
        del blocks