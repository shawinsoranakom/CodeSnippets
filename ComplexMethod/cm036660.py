def layer_norm_ref(
    x,
    weight,
    bias,
    z=None,
    eps=1e-6,
    group_size=None,
    norm_before_gate=True,
    is_rms_norm=False,
):
    """Reference implementation for both layer norm and RMS norm."""
    if is_rms_norm:
        # Use the imported rms_norm_ref for RMS norm cases
        return rms_norm_ref(
            x,
            weight,
            bias,
            z=z,
            eps=eps,
            group_size=group_size,
            norm_before_gate=norm_before_gate,
            upcast=True,
        )

    # Layer norm implementation
    dtype = x.dtype
    x = x.float()
    weight = weight.float()
    bias = bias.float() if bias is not None else None
    z = z.float() if z is not None else None

    if z is not None and not norm_before_gate:
        x = x * F.silu(z)

    if group_size is None:
        # Layer norm: subtract mean
        mean = x.mean(dim=-1, keepdim=True)
        var = ((x - mean).square()).mean(dim=-1, keepdim=True)
        rstd = 1 / torch.sqrt(var + eps)
        out = (x - mean) * rstd * weight
        if bias is not None:
            out = out + bias
    else:
        # Group norm
        from einops import rearrange

        x_group = rearrange(x, "... (g d) -> ... g d", d=group_size)
        mean = x_group.mean(dim=-1, keepdim=True)
        var = ((x_group - mean).square()).mean(dim=-1, keepdim=True)
        rstd = 1 / torch.sqrt(var + eps)
        x_group = (x_group - mean) * rstd
        out = rearrange(x_group, "... g d -> ... (g d)") * weight
        if bias is not None:
            out = out + bias

    if z is not None and norm_before_gate:
        out *= F.silu(z)

    return out.to(dtype)