def to_mxfp(
    data_hp: torch.Tensor,
    block_size: int = 32,
    format: str = "mxfp8",
):
    if data_hp.dtype not in (torch.bfloat16, torch.float):
        raise AssertionError(f"{data_hp.dtype} is not supported yet")
    if data_hp.shape[-1] % block_size != 0:
        raise AssertionError(
            f"the last dimension of shape {data_hp.shape} must be divisible by block_size {block_size}"
        )
    if not data_hp.is_contiguous():
        raise AssertionError("unsupported: data_hp must be contiguous")

    orig_shape = data_hp.shape
    data_hp = data_hp.reshape(
        *orig_shape[:-1], orig_shape[-1] // block_size, block_size
    )

    max_abs = torch.amax(torch.abs(data_hp), -1).unsqueeze(-1)

    data_hp = data_hp.to(torch.float32)
    max_abs = max_abs.to(torch.float32)

    if format == "mxfp8":
        F8E4M3_MAX = torch.finfo(torch.float8_e4m3fn).max  # 448.0
        max_pos = F8E4M3_MAX
    elif format == "mxfp4":
        F4E2M1_MAX = 6.
        max_pos = F4E2M1_MAX

    # RCEIL
    def _to_mx_rceil(
        data_hp: torch.Tensor,
        max_abs: torch.Tensor,
        max_pos: float,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        E8M0_EXPONENT_BIAS = 127
        descale = max_abs / max_pos
        exponent = torch.where(
            torch.isnan(descale),
            0xFF,  # Handle biased exponent for nan
            # NOTE: descale < (torch.finfo(torch.float32).smallest_normal / 2) is handled through clamping
            (
                torch.clamp(
                    torch.ceil(torch.log2(descale)),
                    min=-E8M0_EXPONENT_BIAS,
                    max=E8M0_EXPONENT_BIAS,
                )
                + E8M0_EXPONENT_BIAS
            ).to(torch.uint8),
        )

        descale_fp = torch.where(
            exponent == 0,
            1.0,
            torch.exp2(E8M0_EXPONENT_BIAS - exponent.to(torch.float32)),
        )

        # scale and saturated cast the data elements to max of target dtype
        data_lp = torch.clamp(data_hp * descale_fp, min=-1 * max_pos, max=max_pos)
        return exponent, data_lp

    scale_e8m0_biased, data_lp = _to_mx_rceil(data_hp, max_abs, max_pos)

    # cast to target dtype
    if format == "mxfp8":
        data_lp = data_lp.to(torch.float8_e4m3fn)
        # need to reshape at the end to help inductor fuse things
        data_lp = data_lp.reshape(orig_shape)
    elif format == "mxfp4":
        data_lp = _bfloat16_to_float4_e2m1fn_x2(data_lp.to(torch.bfloat16))
        final_shape = list(orig_shape)
        final_shape[-1] //= 2
        data_lp = data_lp.reshape(final_shape)

    scale_e8m0_biased = scale_e8m0_biased.view(torch.float8_e8m0fnu)
    scale_e8m0_biased = scale_e8m0_biased.squeeze(-1)
    return scale_e8m0_biased, data_lp