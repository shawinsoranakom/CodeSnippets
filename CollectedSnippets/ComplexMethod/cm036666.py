def native_batched_masked_quant_matmul(
    A: torch.Tensor,
    B: torch.Tensor,
    C: torch.Tensor,
    num_expert_tokens: torch.Tensor,
    A_scale: torch.Tensor | None = None,
    B_scale: torch.Tensor | None = None,
    block_shape: list[int] | None = None,
    per_act_token_quant: bool = False,
) -> torch.Tensor:
    num_expert_tokens_cpu = num_expert_tokens.clone()
    num_expert_tokens_cpu = num_expert_tokens_cpu.to(device="cpu")
    num_experts = num_expert_tokens.size(0)

    for e in range(num_experts):
        num_tokens = num_expert_tokens_cpu[e]
        if A.dtype.itemsize == 1 and block_shape is not None:
            assert A_scale is not None and B_scale is not None
            tmp = native_w8a8_block_matmul(
                A[e], B[e], A_scale[e], B_scale[e], block_shape, C.dtype
            )
            C[e, :num_tokens, :] = tmp[:num_tokens, :]
        elif A.dtype.itemsize == 1 and block_shape is None:
            assert A_scale is not None and B_scale is not None
            A_dq = dequant(A[e], A_scale[e], block_shape, per_act_token_quant)
            B_dq = dequant(B[e], B_scale[e], block_shape, per_act_token_quant)
            C[e, :num_tokens, :] = (A_dq[:num_tokens] @ B_dq.transpose(0, 1)).to(
                C.dtype
            )
        else:
            assert A_scale is None
            assert B_scale is None
            C[e, :num_tokens, :] = A[e, :num_tokens, :] @ B[e].transpose(0, 1)

    return C