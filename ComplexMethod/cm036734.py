def test_fused_moe_wn16(
    m: int,
    n: int,
    k: int,
    e: int,
    topk: int,
    ep_size: int,
    dtype: torch.dtype,
    group_size: int,
    has_zp: bool,
    weight_bits: int,
):
    a = torch.randn((m, k), device="cuda", dtype=dtype) / 10
    w1 = torch.randn((e, 2 * n, k), device="cuda", dtype=dtype) / 10
    w2 = torch.randn((e, k, n), device="cuda", dtype=dtype) / 10
    score = torch.randn((m, e), device="cuda", dtype=dtype)

    if weight_bits == 4:
        pack_factor = 2
        quant_type = scalar_types.uint4 if has_zp else scalar_types.uint4b8
    elif weight_bits == 8:
        pack_factor = 1
        quant_type = scalar_types.uint8 if has_zp else scalar_types.uint8b128

    w1_ref = w1.clone()
    w2_ref = w2.clone()
    w1_qweight = torch.empty(
        (e, 2 * n, k // pack_factor), device="cuda", dtype=torch.uint8
    )
    w2_qweight = torch.empty((e, k, n // pack_factor), device="cuda", dtype=torch.uint8)
    w1_scales = torch.empty((e, 2 * n, k // group_size), device="cuda", dtype=dtype)
    w2_scales = torch.empty((e, k, n // group_size), device="cuda", dtype=dtype)
    w1_qzeros = torch.empty(
        (e, 2 * n // pack_factor, k // group_size), device="cuda", dtype=torch.uint8
    )
    w2_qzeros = torch.empty(
        (e, k // pack_factor, n // group_size), device="cuda", dtype=torch.uint8
    )

    for i in range(e * 2):
        expert_id = i % e
        if i // e == 0:
            w, w_ref, w_qweight, w_scales, w_qzeros = (
                w1,
                w1_ref,
                w1_qweight,
                w1_scales,
                w1_qzeros,
            )
        else:
            w, w_ref, w_qweight, w_scales, w_qzeros = (
                w2,
                w2_ref,
                w2_qweight,
                w2_scales,
                w2_qzeros,
            )
        weight, qweight, scales, qzeros = quantize_weights(
            w[expert_id].T, quant_type, group_size, has_zp, False
        )
        weight = weight.T
        qweight = qweight.T.contiguous().to(torch.uint8)
        scales = scales.T
        if has_zp:
            qzeros = qzeros.T.contiguous().to(torch.uint8)
        if weight_bits == 4:
            qweight = qweight[:, 1::2] * 16 + qweight[:, ::2]
            if has_zp:
                qzeros = qzeros[1::2, :] * 16 + qzeros[::2, :]

        w_ref[expert_id] = weight
        w_qweight[expert_id] = qweight
        w_scales[expert_id] = scales
        if has_zp:
            w_qzeros[expert_id] = qzeros

    if ep_size > 1:
        local_e = e // ep_size
        e_ids = torch.randint(0, e, (local_e,), device="cuda", dtype=torch.int32)
        e_map = torch.full((e,), -1, device="cuda", dtype=torch.int32)
        e_map[e_ids] = torch.arange(local_e, device="cuda", dtype=torch.int32)
        w1_ref = w1_ref[e_ids]
        w2_ref = w2_ref[e_ids]
        w1_qweight = w1_qweight[e_ids]
        w2_qweight = w2_qweight[e_ids]
        w1_scales = w1_scales[e_ids]
        w2_scales = w2_scales[e_ids]
        w1_qzeros = w1_qzeros[e_ids]
        w2_qzeros = w2_qzeros[e_ids]
    else:
        e_map = None

    if weight_bits == 4:
        quant_config_builder = int4_w4a16_moe_quant_config
    else:
        assert weight_bits == 8
        quant_config_builder = int8_w8a16_moe_quant_config

    quant_config = quant_config_builder(
        w1_scale=w1_scales,
        w2_scale=w2_scales,
        w1_zp=w1_qzeros if has_zp else None,
        w2_zp=w2_qzeros if has_zp else None,
        block_shape=[0, group_size],
    )

    with set_current_vllm_config(vllm_config):
        triton_output = fused_moe(
            a,
            w1_qweight,
            w2_qweight,
            score,
            topk,
            renormalize=False,
            global_num_experts=e,
            expert_map=e_map,
            quant_config=quant_config,
        )
        torch_output = torch_moe(a, w1_ref, w2_ref, score, topk, expert_map=e_map)

    torch.testing.assert_close(triton_output, torch_output, atol=2e-2, rtol=0)