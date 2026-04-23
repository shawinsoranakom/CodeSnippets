def prep_scale_for_group_broadcast(
    scale: torch.Tensor,
    x: torch.Tensor,
    group_shape: GroupShape | None,
) -> torch.Tensor:
    """
    Prepare the input quantization scale for group broadcasting.

    Args:
        scale: The scale tensor (scalar or 1D).
        x: Target tensor whose shape determines broadcast dimensions.
        group_shape: GroupShape to broadcast over.

    Returns:
        scale reshaped for correct broadcasting.
    """
    if scale.numel() == 1:
        # For per-tensor quant, keep the scale as a scalar (not reshaped to (1, 1)).
        # This avoids misclassifying it as channelwise quant in Fp8LinearOp.apply,
        # where the "per_tensor_activations" check relies on "x_scale.dim() < 2":
        #   per_tensor_activations = (x_scale.numel() == 1) and x_scale.dim() < 2
        # For all other cases, reshape scalar scales to (1, 1) for broadcasting.
        return (
            scale
            if group_shape is not None and group_shape.is_per_tensor()
            else scale.reshape(1, 1)
        )
    if scale.ndim == 1:
        assert group_shape is not None, (
            "group_shape must be provided to correctly broadcast 1D scale"
        )
        rows, cols = _normalize_quant_group_shape(x, group_shape)
        # Determine broadcasting dimension: either rows or columns match group size
        if rows == x.shape[-2]:
            scale = scale.unsqueeze(-2)
        elif cols == x.shape[-1]:
            scale = scale.unsqueeze(-1)
        else:
            raise ValueError(
                f"1D scale with shape {scale.shape} cannot be broadcast to x with shape"
                f" {x.shape}, group_shape={(rows, cols)}"
            )
    return scale