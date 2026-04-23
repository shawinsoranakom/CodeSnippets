def batched_moe_kernel_quantize_input(
    A: torch.Tensor,
    A_scale: torch.Tensor | None,
    num_tokens: int,
    E: int,
    N: int,
    expert_num_tokens: torch.Tensor,
    qtype: torch.dtype | None,
    per_act_token_quant: bool,
    block_shape: list[int] | None = None,
) -> tuple[torch.Tensor, torch.Tensor | None]:
    if torch.compiler.is_compiling() or torch.cuda.is_current_stream_capturing():
        # Note: this does a bunch of extra work because expert_num_tokens is
        # ignored but it does support torch.compile + cudagraphs.
        hidden_dim = A.size(-1)
        assert A_scale is None or A_scale.ndim <= 2, (
            f"{A_scale.shape if A_scale is not None else None}"
        )
        A_q, A_q_scale = moe_kernel_quantize_input(
            A.view(-1, hidden_dim), A_scale, qtype, per_act_token_quant, block_shape
        )
        A_q = A_q.view(E, -1, hidden_dim)
        A_q_scale = normalize_batched_scales_shape(A_q_scale, E)

        return A_q, A_q_scale
    elif qtype is None:
        return A, normalize_batched_scales_shape(A_scale, E)
    else:
        A_q = torch.empty_like(A, dtype=qtype)

        if per_act_token_quant:
            assert block_shape is None
            scale_shape = (E, num_tokens, 1)
        elif block_shape is not None:
            _, block_k = block_shape
            k_tiles = (A.shape[-1] + block_k - 1) // block_k
            scale_shape = (E, num_tokens, k_tiles)
        else:
            scale_shape = (E, 1, 1)

        A_q_scale = torch.zeros(scale_shape, dtype=torch.float32, device=A.device)

        num_experts = expert_num_tokens.numel()

        A_scale = normalize_batched_scales_shape(A_scale, num_experts)

        for e in range(E):
            num_tokens = int(expert_num_tokens[e].item())
            if num_tokens > 0:
                if A_scale is not None:
                    scales = A_scale[e, : min(num_tokens, A_scale.shape[1])]
                else:
                    scales = None
                A_q[e, :num_tokens], tmp_scale = moe_kernel_quantize_input(
                    A[e, :num_tokens],
                    scales,
                    qtype,
                    per_act_token_quant,
                    block_shape,
                )
                assert tmp_scale is not None
                A_q_scale[e, : tmp_scale.shape[0]] = tmp_scale

        return A_q, A_q_scale