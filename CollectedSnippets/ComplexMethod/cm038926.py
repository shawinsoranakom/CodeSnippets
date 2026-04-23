def marlin_create_bench_fn(bt: BenchmarkTensors) -> Callable:
    device = bt.a.device

    workspace = MarlinWorkspace(
        bt.w_ref.shape[1], GPTQ_MARLIN_MIN_THREAD_N, GPTQ_MARLIN_MAX_PARALLEL
    )

    if bt.w_g_zp is None:
        w_zp = torch.empty(0, dtype=torch.int, device=device)
    else:
        w_zp = marlin_zero_points(
            bt.w_g_zp, bt.w_ref.shape[0], bt.w_ref.shape[1], bt.wtype.size_bits
        )

    if bt.group_size is None:
        w_s = torch.tensor([], device="cuda", dtype=torch.half)
    else:
        w_s = marlin_permute_scales(
            bt.w_g_s, bt.w_ref.shape[0], bt.w_ref.shape[1], bt.group_size
        )

    sort_indices = torch.empty(0, dtype=torch.int, device=device)
    g_idx = torch.empty(0, dtype=torch.int, device=device)
    w_q = ops.gptq_marlin_repack(
        bt.w_q, sort_indices, bt.w_ref.shape[0], bt.w_ref.shape[1], bt.wtype.size_bits
    )

    if bt.a.dtype.is_floating_point:
        assert bt.w_ch_s is None
        assert bt.w_tok_s is None
        assert bt.group_size is not None

        fn = lambda: ops.marlin_gemm(
            a=bt.a,
            c=None,
            b_q_weight=w_q,
            b_bias=None,
            b_scales=w_s,
            a_scales=None,
            global_scale=None,
            b_zeros=w_zp,
            g_idx=g_idx,
            perm=sort_indices,
            workspace=workspace.scratch,
            b_q_type=bt.wtype,
            size_m=bt.a.shape[0],
            size_n=bt.w_ref.shape[1],
            size_k=bt.w_ref.shape[0],
            is_k_full=True,
            is_zp_float=False,
        )
    else:
        assert bt.a.dtype == torch.int8
        assert bt.wtype == scalar_types.uint4b8
        raise NotImplementedError("QQQ is not supported anymore")

    return fn