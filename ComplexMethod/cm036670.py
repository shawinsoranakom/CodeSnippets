def create_test_tensors(
    shape: tuple[int, int, int],
    types: TypeConfig,
    group_size: int | None,
    subset_stride_factor: int | None = None,
) -> Tensors:
    m, n, k = shape
    factor = subset_stride_factor or 1

    print(
        "create_test_tensors, shape:", shape, "types:", types, "group_size:", group_size
    )

    a = rand_data((m * factor, k * factor), types.act_type, scale=3, offset=2)
    w = rand_data((k * factor, n * factor), types.act_type, scale=3, offset=1)

    if factor > 1:
        a = a[0:m, 0:k]
        w = w[0:k, 0:n]

    if types.group_scale_type is not None:
        w = w.to(types.group_scale_type)
    if w.dtype.itemsize == 1:
        w = w.to(torch.float16)

    w_ref, w_q_packed, w_s, w_zp = machete_quantize_and_pack(
        a.dtype,
        w,
        types.weight_type,
        types.group_scale_type,
        group_size,
        types.group_zero_type is not None,
    )

    if not a.dtype.is_floating_point:
        aiinfo = torch.iinfo(a.dtype)
        w_ref = w_ref.round().clamp(aiinfo.min, aiinfo.max)

    a_ref = a.to(torch.float32)
    w_ref = w_ref.to(torch.float32)

    w_ch_s = (
        None
        if types.channel_scale_type is None
        else rand_data((n,), types.channel_scale_type)
    )
    w_tok_s = (
        None
        if types.token_scale_type is None
        else rand_data((m,), types.token_scale_type)
    )

    return Tensors(
        w_ref=w_ref,
        a_ref=a_ref,
        a=a,
        w_q=w_q_packed,
        w_g_s=w_s,
        w_g_zp=maybe_convert_zeropoints(w_zp, w_s),
        w_ch_s=w_ch_s,
        w_tok_s=w_tok_s,
    )