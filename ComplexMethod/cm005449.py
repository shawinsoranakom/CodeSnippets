def _can_use_grouped_mm(input: torch.Tensor, weight: torch.Tensor, offs: torch.Tensor) -> bool:
    """
    Check if torch.nn.functional.grouped_mm or torch._grouped_mm can be used based on availability and compatibility with torch.compile.

    Args:
        input (`torch.Tensor`):
            Input tensor of shape (S, input_dim).
        weight (`torch.Tensor`):
            Weight tensor of shape (num_experts, input_dim, output_dim).
        offs (`torch.Tensor`):
            Offsets tensor indicating the boundaries of each group in the input tensor.
    Returns:
        `bool`: True if grouped_mm can be used, False otherwise.
    """
    if (is_torchdynamo_compiling() and weight.dtype != torch.bfloat16) or (
        weight.device.type == "cpu"
        # accept_dev=True is necessary for "+cpu"/"+xpu" etc.
        and is_torch_less_or_equal("2.10.0", accept_dev=True)
        and (weight.data_ptr() % 16 != 0 or input.data_ptr() % 16 != 0)
    ):
        # Under the following conditions we cannot use torch.grouped_mm and have to fall back:
        # 1. torch.grouped_mm is not supported in torch.compile / inductor with dtypes other than bf16
        # 2. Before PyTorch 2.11, torch.grouped_mm on CPU required 16 bytes alignment which is not
        #    guaranteed for tensors loaded using memmap (e.g. using safetensors lazy tensor loading)
        #    and not really necessary because the cpu path uses a fallback for-loop implementation.
        #    issue: https://github.com/pytorch/pytorch/issues/172440
        return False

    # On CUDA, `grouped_mm` availability also depends on GPU compute capability:
    # `torch.nn.functional.grouped_mm` in torch>=2.10 and `torch._grouped_mm` in torch>=2.9 support SM80+
    # but older `torch._grouped_mm` requires SM90+.
    if weight.device.type == "cuda":
        if hasattr(torch.nn.functional, "grouped_mm"):
            return torch.cuda.get_device_capability(weight.device) >= (8, 0)
        if hasattr(torch, "_grouped_mm"):
            if is_torch_greater_or_equal("2.9", accept_dev=True):
                return torch.cuda.get_device_capability(weight.device) >= (8, 0)
            else:
                return torch.cuda.get_device_capability(weight.device) >= (9, 0)

        return False

    return hasattr(torch.nn.functional, "grouped_mm") or hasattr(torch, "_grouped_mm")