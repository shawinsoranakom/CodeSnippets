def _w4a16_reference(
    a_mk: torch.Tensor,
    b_packed_kn8: torch.Tensor,
    scales_gn: torch.Tensor,
    *,
    group_size: int,
    qzeros_gn8: torch.Tensor | None,
    zp_bias: int,
) -> torch.Tensor:
    """Reference implementation for W4A16.

    a_mk: [M,K] fp16/bf16
    b_packed_kn8: [K, N//8] int32, N-packed int4 weights
    scales_gn: [K//G, N] fp16/bf16
    qzeros_gn8: [K//G, N//8] int32, N-packed int4 zeros, or None
    """
    assert a_mk.dtype in (torch.float16, torch.bfloat16)
    assert b_packed_kn8.dtype == torch.int32
    assert scales_gn.dtype == a_mk.dtype

    M, K = a_mk.shape
    N = b_packed_kn8.shape[1] * 8
    assert b_packed_kn8.shape[0] == K

    assert group_size > 0 and K % group_size == 0
    G = group_size
    num_groups = K // G
    assert scales_gn.shape == (num_groups, N)

    w_int4 = _unpack_int4_along_n(b_packed_kn8)  # [K,N]
    if qzeros_gn8 is None:
        z_full = torch.full((K, N), zp_bias, dtype=torch.int32, device=a_mk.device)
    else:
        assert qzeros_gn8.shape == (num_groups, N // 8)
        z_gn = _unpack_int4_along_n(qzeros_gn8)  # [G,N] in groups
        z_full = z_gn.repeat_interleave(G, dim=0)  # [K,N]

    s_full = scales_gn.repeat_interleave(G, dim=0).to(torch.float32)  # [K,N]
    w_fp = (w_int4 - z_full).to(torch.float32) * s_full  # [K,N]

    out = a_mk.to(torch.float32) @ w_fp  # [M,N]
    return out.to(a_mk.dtype)