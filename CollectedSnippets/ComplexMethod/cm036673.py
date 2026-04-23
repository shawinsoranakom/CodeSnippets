def make_moe_test_setup(
    num_experts: int,
    K: int,
    N: int,
    *,
    alignment: int = ALIGNMENT,
    max_blocks: int = 64,
    device: str = "cuda",
    random_zero: bool = False,
) -> MoETestSetup:
    """Create a full set of tensors for testing cutlass_w4a8_moe_mm."""

    assert K % GROUP_SIZE == 0
    # Token counts per expert (multiples of `alignment`).
    Ms = [alignment * random.randint(1, max_blocks) for _ in range(num_experts)]

    # set random experts to 0 tokens
    if random_zero and num_experts > 1:
        num_zero = max(1, num_experts // 8)
        zero_indices = random.sample(range(num_experts), k=num_zero)
        for idx in zero_indices:
            Ms[idx] = 0

    M_full = sum(Ms)
    assert M_full > 0

    # Activations.
    a = to_fp8(torch.randn((M_full, K), device=device))
    a_ref = a.to(torch.float32)
    a_strides = torch.full((num_experts,), K, dtype=torch.int64, device=device)

    # Output buffer.
    out = torch.empty((M_full, N), dtype=torch.bfloat16, device=device)
    c_strides = torch.full((num_experts,), N, dtype=torch.int64, device=device)

    # Channel/token scales.
    per_tok_scales = torch.randn((M_full, 1), dtype=torch.float32, device=device)
    per_chan_scales = torch.randn(
        (num_experts, N, 1), dtype=torch.float32, device=device
    )

    # Expert weights and scales.
    wtype = scalar_types.int4
    atype = stype = torch.float8_e4m3fn
    w_refs, w_qs, w_ss = [], [], []
    for _ in range(num_experts):
        b = to_fp8(torch.randn((K, N), device=device))
        w_ref, w_q, w_s, _ = cutlass_quantize(
            atype, b.to(torch.float16), wtype, stype, GROUP_SIZE, zero_points=False
        )
        w_refs.append(w_ref)
        w_qs.append(w_q)
        w_ss.append(w_s)

    w_q_packed, w_s_packed, packed_layout = cutlass_preprocess(w_qs, w_ss)

    problem_sizes = torch.tensor(
        [[N, M, K] for M in Ms], dtype=torch.int32, device=device
    )

    expert_offsets = torch.cat(
        [
            torch.tensor([0], dtype=torch.int64),
            torch.cumsum(torch.tensor(Ms, dtype=torch.int64), dim=0)[:-1],
        ]
    ).to(device=device)

    # B strides and group scale strides.
    b_strides = packed_layout
    group_scale_strides = torch.zeros(
        (num_experts, 2), dtype=torch.int64, device=device
    )
    group_scale_strides[:, 0] = N

    return MoETestSetup(
        num_experts=num_experts,
        K=K,
        N=N,
        Ms=Ms,
        M_full=M_full,
        a=a,
        a_ref=a_ref,
        a_strides=a_strides,
        out=out,
        c_strides=c_strides,
        per_tok_scales=per_tok_scales,
        per_chan_scales=per_chan_scales,
        w_refs=w_refs,
        w_q_packed=w_q_packed,
        w_s_packed=w_s_packed,
        problem_sizes=problem_sizes,
        expert_offsets=expert_offsets,
        b_strides=b_strides,
        group_scale_strides=group_scale_strides,
    )