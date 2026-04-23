def _test_grouped_gemm_forward(
    data_config: DataConfig,
    model_config: ModelConfig,
    permute_x: bool,
    permute_y: bool,
    use_W1: bool,  # W1 -> first grouped GEMM in a fused MoE MLP, not W1 -> second grouped GEMM in a fused MoE MLP
    fuse_mul_post: bool = False,
    flatten: bool = True,
    # Manually tuned parameters
    use_tma_load_w: bool = False,
    use_tma_load_x: bool = False,
    use_tma_store: bool = False,
    BLOCK_SIZE_M: int = None,
    BLOCK_SIZE_N: int = None,
    BLOCK_SIZE_K: int = None,
    num_warps: int = None,
    num_stages: int = None,
    # Autotuning parameters
    autotune: bool = False,
    num_autotune_configs: int = None,
    # Flag to manually enable TMA store
    allow_tma_store: bool = False,
    use_autograd: bool = False,
):
    if not check_valid_config(
        permute_x, permute_y, use_W1 = use_W1, fuse_mul_post = fuse_mul_post
    ):
        pytest.skip(
            f"Skipping test due to invalid config: {permute_x = } {permute_y = } {use_W1 = } {fuse_mul_post = }"
        )

    if use_tma_store and not allow_tma_store:
        pytest.skip("TMA store needs to be debugged due to non-deterministic behavior")

    X1, X2, W1, W2, gating_output = make_inputs(
        M = data_config.bs * data_config.seq_len,
        N = model_config.intermediate_size,
        K = model_config.hidden_size,
        E = model_config.num_experts,
        topk = model_config.topk,
        dtype = data_config.dtype,
    )
    topk = model_config.topk
    use_sigmoid = model_config.use_sigmoid
    renormalize = model_config.renormalize

    X = X1 if use_W1 else X2
    num_tokens = data_config.bs * data_config.seq_len
    E, K, N = W2.shape  # E = num_experts, K = hidden_size, N = intermediate_size
    assert W1.shape == (E, 2 * N, K)
    W = W1 if use_W1 else W2

    if use_W1:
        assert X.shape == (
            num_tokens,
            K,
        ), f"X.shape: {X.shape}, num_tokens: {num_tokens}, K: {K}"
    else:
        assert X.shape == (
            num_tokens * topk,
            N,
        ), f"X.shape: {X.shape}, num_tokens: {num_tokens}, topk: {topk}, N: {N}"

    total_tokens = num_tokens * topk
    output_shape = (total_tokens, 2 * N) if use_W1 else (total_tokens, K)

    topk_weights, topk_ids = calculate_topk(
        gating_output, topk, use_sigmoid = use_sigmoid, renormalize = renormalize
    )
    topk_weights = topk_weights.view(-1)  # num_tokens * topk
    topk_ids = topk_ids.view(-1)  # num_tokens * topk

    expert_token_counts, gather_indices = get_routing_indices(topk_ids, num_experts = E)
    assert len(gather_indices) == total_tokens
    assert len(expert_token_counts) == E

    atol, rtol = TOLERANCE[X.dtype]

    Xperm = permute(X, gather_indices, topk)

    Xref = Xperm

    assert (
        Xperm.shape == (total_tokens, K) if use_W1 else (total_tokens, N)
    ), f"Xperm.shape: {Xperm.shape}, total_tokens: {total_tokens}, K: {K}"

    ref_output = torch_grouped_gemm(X = Xref, W = W, m_sizes = expert_token_counts)

    if permute_x:
        X_test = X
    else:
        X_test = Xperm

    # No need to run all configs for tests, otherwise takes too long
    if autotune:
        from grouped_gemm.kernels.forward import _autotuned_grouped_gemm_forward_kernel

        if num_autotune_configs is not None:
            _autotuned_grouped_gemm_forward_kernel.configs = (
                _autotuned_grouped_gemm_forward_kernel.configs[:num_autotune_configs]
            )

    # Use autograd.Function interface
    if use_autograd:
        from grouped_gemm.interface import grouped_gemm

        kernel_config_fwd = KernelConfigForward(
            BLOCK_SIZE_M = BLOCK_SIZE_M,
            BLOCK_SIZE_N = BLOCK_SIZE_N,
            BLOCK_SIZE_K = BLOCK_SIZE_K,
            num_warps = num_warps,
            num_stages = num_stages,
            permute_x = permute_x,
            permute_y = permute_y,
            fuse_mul_post = fuse_mul_post,
            use_tma_load_w = use_tma_load_w,
            use_tma_load_x = use_tma_load_x,
            use_tma_store = use_tma_store,
        )

        test_output = grouped_gemm(
            X = X_test,
            W = W,
            topk = topk,
            m_sizes = expert_token_counts,
            gather_indices = gather_indices,
            topk_weights = topk_weights if fuse_mul_post else None,
            permute_x = permute_x,
            permute_y = permute_y,
            fuse_mul_post = fuse_mul_post,
            kernel_config_fwd = kernel_config_fwd,
            autotune = autotune,
            is_first_gemm = use_W1,
        )
    # Use manual interface
    else:
        test_output = grouped_gemm_forward(
            X = X_test,
            W = W,
            topk = topk,
            m_sizes = expert_token_counts,
            gather_indices = gather_indices,
            topk_weights = topk_weights if fuse_mul_post else None,
            permute_x = permute_x,
            permute_y = permute_y,
            fuse_mul_post = fuse_mul_post,
            use_tma_load_w = use_tma_load_w,
            use_tma_load_x = use_tma_load_x,
            use_tma_store = use_tma_store,
            autotune = autotune,
            BLOCK_SIZE_M = BLOCK_SIZE_M,
            BLOCK_SIZE_N = BLOCK_SIZE_N,
            BLOCK_SIZE_K = BLOCK_SIZE_K,
            num_warps = num_warps,
            num_stages = num_stages,
            flatten = flatten,
        )
    assert ref_output.shape == output_shape
    assert test_output.shape == output_shape

    if permute_y:
        ref_output = unpermute(ref_output, gather_indices)
    if fuse_mul_post:
        # if we don't permute_y, then test output is permuted with topk weights applied
        # the ref output needs to be unpermuted before multiplying by topk weights since topk weights are in token order
        if not permute_y:
            ref_output = unpermute(ref_output, gather_indices)
            test_output = unpermute(test_output, gather_indices)
        ref_output = ref_output * topk_weights[:, None]

    assert torch.allclose(
        ref_output, test_output, atol = atol, rtol = rtol
    ), f"Grouped gemm forward failed: {(ref_output - test_output).abs().max().item():.6f}"