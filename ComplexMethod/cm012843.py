def determine_qparams(
    min_val: torch.Tensor,
    max_val: torch.Tensor,
    quant_min: int,
    quant_max: int,
    dtype: torch.dtype,
    eps: torch.Tensor,
    has_customized_qrange: bool,
    qscheme: torch.qscheme = torch.per_tensor_affine,
) -> tuple[torch.Tensor, torch.Tensor]:
    r"""Calculates the quantization parameters, given min and max
    value tensors. Works for both per tensor and per channel cases

    Args:
        min_val: Minimum values per channel
        max_val: Maximum values per channel

    Returns:
        scales: Scales tensor of shape (#channels,)
        zero_points: Zero points tensor of shape (#channels,)
    """
    if not check_min_max_valid(min_val, max_val):
        return torch.tensor([1.0], device=min_val.device.type), torch.tensor(
            [0], device=min_val.device.type
        )

    min_val_neg = torch.min(min_val, torch.zeros_like(min_val))
    max_val_pos = torch.max(max_val, torch.zeros_like(max_val))

    device = min_val_neg.device
    scale = torch.ones(min_val_neg.size(), dtype=torch.double, device=device)
    zero_point = torch.zeros(min_val_neg.size(), dtype=torch.int64, device=device)
    eps = eps.to(device)

    if qscheme == torch.per_tensor_symmetric or qscheme == torch.per_channel_symmetric:
        max_val_pos = torch.max(-min_val_neg, max_val_pos)
        scale = max_val_pos / (float(quant_max - quant_min) / 2)
        scale = torch.max(scale, eps)
        if dtype in [torch.uint8, torch.quint8]:
            if has_customized_qrange:
                # When customized quantization range is used, down-rounded midpoint of the range is chosen.
                zero_point = zero_point.new_full(
                    zero_point.size(), (quant_min + quant_max) // 2
                )
            else:
                zero_point = zero_point.new_full(zero_point.size(), 128)
    elif qscheme == torch.per_channel_affine_float_qparams:
        scale = (max_val - min_val) / float(quant_max - quant_min)
        scale = torch.where(scale > eps, scale, torch.ones_like(scale))
        # We use the quantize function
        # xq = Round(Xf * inv_scale + zero_point),
        # setting zero_point to (-1 * min *inv_scale) we get
        # Xq = Round((Xf - min) * inv_scale)
        zero_point = -1 * min_val / scale
    else:
        scale = (max_val_pos - min_val_neg) / float(quant_max - quant_min)
        scale = torch.max(scale, eps)
        zero_point = quant_min - torch.round(min_val_neg / scale).to(torch.int)
        zero_point = torch.clamp(zero_point, quant_min, quant_max)

    # For scalar values, cast them to Tensors of size 1 to keep the shape
    # consistent with default values in FakeQuantize.
    if len(scale.shape) == 0:
        # TODO: switch to scale.item() after adding JIT support
        scale = torch.tensor([float(scale)], dtype=scale.dtype, device=device)
    if len(zero_point.shape) == 0:
        # TODO: switch to zero_point.item() after adding JIT support
        zero_point = torch.tensor(
            [int(zero_point)], dtype=zero_point.dtype, device=device
        )
        if qscheme == torch.per_channel_affine_float_qparams:
            zero_point = torch.tensor(
                [float(zero_point)], dtype=zero_point.dtype, device=device
            )

    return scale.to(torch.double), zero_point.to(torch.int64)