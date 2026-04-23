def torch_experts(
    a: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    topk_weight: torch.Tensor,
    topk_ids: torch.Tensor,
    global_num_experts: int = -1,
    b_bias1: torch.Tensor | None = None,
    b_bias2: torch.Tensor | None = None,
    expert_map: torch.Tensor | None = None,
    w1_scale: torch.Tensor | None = None,
    w2_scale: torch.Tensor | None = None,
    a1_scale: torch.Tensor | None = None,
    a2_scale: torch.Tensor | None = None,
    quant_dtype: torch.dtype | None = None,
    per_act_token_quant=False,
    block_shape: list[int] | None = None,
    apply_router_weights_on_input: bool = False,
    activation: MoEActivation = MoEActivation.SILU,
) -> torch.Tensor:
    assert (
        global_num_experts == -1
        or (global_num_experts == w1.shape[0] and expert_map is None)
        or (expert_map is not None and global_num_experts == expert_map.shape[0])
    )

    if quant_dtype in [torch.float16, torch.bfloat16]:
        quant_dtype = None
    quant_input_only = quant_dtype is not None and w1_scale is None and w2_scale is None
    if quant_input_only:
        assert a1_scale is None and a2_scale is None
        assert per_act_token_quant

    M, K = a.shape
    topk = topk_ids.shape[1]

    if apply_router_weights_on_input:
        assert topk == 1
        a = a * topk_weight.to(a.dtype)

    a = a.view(M, -1, K).repeat(1, topk, 1).reshape(-1, K)

    out = torch.zeros(M * topk, w2.shape[1], dtype=a.dtype, device=a.device)

    if a1_scale:
        assert not per_act_token_quant and block_shape is None
    a, a_scale = moe_kernel_quantize_input(
        a, a1_scale, quant_dtype, per_act_token_quant, block_shape
    )

    if quant_input_only:
        a = (a.float() * a_scale.view(-1, 1)).to(w1.dtype)

    num_experts = w1.shape[0]

    topk_ids = topk_ids.view(-1)
    if expert_map is not None:
        topk_ids = expert_map[topk_ids]

    f32 = torch.float32

    act = op_registry[activation.custom_op_name]

    for i in range(num_experts):
        mask = topk_ids == i
        if mask.sum():
            if quant_dtype is None:
                tmp1 = a[mask] @ w1[i].transpose(0, 1)
                if b_bias1 is not None:
                    tmp1 = tmp1 + b_bias1[i].view(1, -1).to(tmp1.dtype)
                tmp2 = act()(tmp1)
                out[mask] = tmp2 @ w2[i].transpose(0, 1)
                if b_bias2 is not None:
                    out[mask] = out[mask] + b_bias2[i].view(1, -1).to(tmp1.dtype)
            elif quant_input_only:
                tmp1 = a[mask] @ w1[i].transpose(0, 1)
                tmp2 = SiluAndMul()(tmp1)
                tmp2, tmp2_scale = moe_kernel_quantize_input(
                    tmp2, None, quant_dtype, per_act_token_quant
                )
                tmp2 = (tmp2.float() * tmp2_scale.view(-1, 1)).to(w2.dtype)
                out[mask] = tmp2 @ w2[i].transpose(0, 1)
            elif block_shape is not None:
                # block quantized
                assert (
                    a_scale is not None
                    and w1_scale is not None
                    and w2_scale is not None
                )
                tmp1 = native_w8a8_block_matmul(
                    a[mask], w1[i], a_scale[mask], w1_scale[i], block_shape, out.dtype
                )
                if b_bias1 is not None:
                    tmp1 = tmp1 + b_bias1[i].view(1, -1).to(tmp1.dtype)
                tmp2 = SiluAndMul()(tmp1)
                tmp2, b_scale = moe_kernel_quantize_input(
                    tmp2, a2_scale, quant_dtype, per_act_token_quant, block_shape
                )

                out[mask] = native_w8a8_block_matmul(
                    tmp2, w2[i], b_scale, w2_scale[i], block_shape, out.dtype
                )
                if b_bias2 is not None:
                    out[mask] = out[mask] + b_bias2[i].view(1, -1).to(tmp1.dtype)
            else:
                assert (
                    a_scale is not None
                    and w1_scale is not None
                    and w2_scale is not None
                )
                scales = a_scale if a_scale.numel() == 1 else a_scale[mask]

                tmp1 = a[mask].to(f32) * scales
                w1_dq = (w1[i].to(f32) * w1_scale[i]).transpose(0, 1)
                tmp1 = (tmp1 @ w1_dq).to(out.dtype)
                if b_bias1 is not None:
                    tmp1 = tmp1 + b_bias1[i].view(1, -1).to(out.dtype)

                tmp2 = act()(tmp1).to(out.dtype)

                tmp2, b_scale = moe_kernel_quantize_input(
                    tmp2, a2_scale, quant_dtype, per_act_token_quant, block_shape
                )
                assert b_scale is not None

                tmp2 = tmp2.to(f32) * b_scale
                w2_dq = (w2[i].to(f32) * w2_scale[i]).transpose(0, 1)
                out[mask] = (tmp2 @ w2_dq).to(out.dtype)
                if b_bias2 is not None:
                    out[mask] = out[mask] + b_bias2[i].view(1, -1).to(out.dtype)

    if apply_router_weights_on_input:
        return out
    else:
        return (
            (out.view(M, -1, w2.shape[1]).to(f32) * topk_weight.view(M, -1, 1))
            .sum(dim=1)
            .to(out.dtype)
        )