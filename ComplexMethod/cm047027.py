def _test_grouped_gemm_backward_dW(
    data_config: DataConfig,
    model_config: ModelConfig,
    permute_x: bool,
    permute_y: bool,
    use_W1: bool,
    use_tma_load_dy: bool = False,
    use_tma_load_x: bool = False,
    use_tma_store: bool = False,
    BLOCK_SIZE_M: int = None,
    BLOCK_SIZE_N: int = None,
    BLOCK_SIZE_K: int = None,
    num_warps: int = None,
    num_stages: int = None,
    flatten: bool = True,
    autotune: bool = False,
    num_autotune_configs: int = None,
    allow_tma_store: bool = False,
    debug: bool = False,
    fuse_mul_post: bool = False,  # Unused for backward_dW
    use_autograd: bool = False,
):
    if not check_valid_config(
        permute_x,
        permute_y,
        fuse_mul_post = fuse_mul_post,
        use_W1 = use_W1,
        is_backward = True,
    ):
        pytest.skip(
            f"Skipping test due to invalid config: {permute_x = } {permute_y = } {use_W1 = }"
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
        requires_grad = True,
    )
    topk = model_config.topk
    num_experts = model_config.num_experts
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

    X_test = X.detach().clone().requires_grad_(True)
    W_test = W.detach().clone().requires_grad_(True)

    topk_weights, topk_ids = calculate_topk(
        gating_output, topk, use_sigmoid = use_sigmoid, renormalize = renormalize
    )
    topk_weights = topk_weights.view(-1)  # num_tokens * topk
    topk_ids = topk_ids.view(-1)  # num_tokens * topk

    expert_token_counts, gather_indices = get_routing_indices(topk_ids, num_experts = E)
    assert len(gather_indices) == total_tokens
    assert len(expert_token_counts) == num_experts

    atol, rtol = TOLERANCE[X.dtype]
    Xperm = permute(X, gather_indices, topk)
    Xperm_test = Xperm.detach().clone().requires_grad_(True)

    # Need to retain grad otherwise grad is not propagated
    X.retain_grad()
    W.retain_grad()
    Xperm.retain_grad()
    assert Xperm.shape == (total_tokens, K) if use_W1 else (total_tokens, N)

    output_shape = (total_tokens, 2 * N) if use_W1 else (total_tokens, K)

    ref_output = torch_grouped_gemm(X = Xperm, W = W, m_sizes = expert_token_counts)
    assert ref_output.shape == output_shape

    # if permute_y then the assumption is that the output of grouped_gemm was unpermuted on store
    # Therefore we have to unpermute before backpropping to ensure proper alignment
    if permute_y:
        ref_output = unpermute(ref_output, gather_indices)

    grad_output = torch.randn_like(ref_output)
    ref_output.backward(grad_output)
    assert X.grad is not None
    assert W.grad is not None

    # Test backward kernel directly
    X_ = X_test if permute_x else Xperm_test

    if debug:
        torch.set_printoptions(precision = 4)
        for i in range(num_experts):
            print(f"Expert {i} weight grad:\n{W.grad[i, :5, :5]}")

    if autotune:
        from grouped_gemm.kernels.backward import _autotuned_grouped_gemm_dW_kernel

        if num_autotune_configs is not None:
            _autotuned_grouped_gemm_dW_kernel.configs = (
                _autotuned_grouped_gemm_dW_kernel.configs[:num_autotune_configs]
            )

    if use_autograd:
        from grouped_gemm.interface import grouped_gemm

        if not autotune:
            kernel_config_fwd = KernelConfigForward(
                # Only care about backward_dW config
                use_tma_load_w = False,
                use_tma_load_x = False,
                use_tma_store = False,
                BLOCK_SIZE_M = BLOCK_SIZE_M,
                BLOCK_SIZE_N = BLOCK_SIZE_N,
                BLOCK_SIZE_K = BLOCK_SIZE_K,
                num_warps = num_warps,
                num_stages = num_stages,
            )
            kernel_config_bwd_dW = KernelConfigBackward_dW(
                use_tma_load_dy = use_tma_load_dy,
                use_tma_load_x = use_tma_load_x,
                use_tma_store = use_tma_store,
                BLOCK_SIZE_M = BLOCK_SIZE_M,
                BLOCK_SIZE_N = BLOCK_SIZE_N,
                BLOCK_SIZE_K = BLOCK_SIZE_K,
                num_warps = num_warps,
                num_stages = num_stages,
            )
        else:
            from grouped_gemm.kernels.backward import _autotuned_grouped_gemm_dW_kernel
            from grouped_gemm.kernels.forward import (
                _autotuned_grouped_gemm_forward_kernel,
            )

            if num_autotune_configs is not None:
                _autotuned_grouped_gemm_forward_kernel.configs = (
                    _autotuned_grouped_gemm_forward_kernel.configs[
                        :num_autotune_configs
                    ]
                )
                _autotuned_grouped_gemm_dW_kernel.configs = (
                    _autotuned_grouped_gemm_dW_kernel.configs[:num_autotune_configs]
                )
            kernel_config_fwd = None
            kernel_config_bwd_dW = None

        test_output = grouped_gemm(
            X = X_,
            W = W_test,
            m_sizes = expert_token_counts,
            gather_indices = gather_indices,
            topk = topk,
            permute_x = permute_x,
            permute_y = permute_y,
            kernel_config_fwd = kernel_config_fwd,
            kernel_config_bwd_dW = kernel_config_bwd_dW,
            autotune = autotune,
            is_first_gemm = use_W1,
            dW_only = True,
        )
        assert (
            test_output.shape == ref_output.shape
        ), f"Grouped gemm autograd backward_dW outputs mismatch: {test_output.shape} != {ref_output.shape}"
        assert torch.allclose(
            test_output, ref_output, atol = atol, rtol = rtol
        ), f"Grouped gemm autograd backward_dW forward outputs mismatch: {test_output.shape} != {ref_output.shape}"
        test_output.backward(grad_output)
        assert W_test.grad is not None
        dW_test = W_test.grad
    else:
        dW_test = grouped_gemm_dW(
            dY = grad_output,
            X = X_,
            m_sizes = expert_token_counts,
            gather_indices = gather_indices,
            topk = topk,
            permute_x = permute_x,
            permute_y = permute_y,
            use_tma_load_dy = use_tma_load_dy,
            use_tma_load_x = use_tma_load_x,
            use_tma_store = use_tma_store,
            BLOCK_SIZE_M = BLOCK_SIZE_M,
            BLOCK_SIZE_N = BLOCK_SIZE_N,
            BLOCK_SIZE_K = BLOCK_SIZE_K,
            num_warps = num_warps,
            num_stages = num_stages,
            flatten = flatten,
            autotune = autotune,
            debug = debug,
        )
    assert (
        W.grad.shape == dW_test.shape
    ), f"Grouped gemm manual backward_dW outputs mismatch: W.grad: {W.grad.shape}, dW_test: {dW_test.shape}"

    if debug:
        with torch.no_grad():
            if not torch.allclose(W.grad, dW_test, atol = atol, rtol = rtol):
                print(f"Ref Wgrad sum: {W.grad.sum().item():.4f}")
            print(f"Test Wgrad sum: {dW_test.sum().item():.4f}")

            for i in range(num_experts):
                print(f"Expert {i} weight grad:\n{W.grad[i, :5, :5]}")
                print(f"Expert {i} dW_test:\n{dW_test[i, :5, :5]}")
                expert_diff = (W.grad[i, :, :] - dW_test[i, :, :]).abs().max().item()
                print(f"Expert {i} diff: {expert_diff:.6f}")

            diff = (W.grad - dW_test).abs().max().item()
            assert (
                False
            ), f"Grouped gemm manual backward_dW outputs mismatch: {diff:.6f}"
    else:
        diff = (W.grad - dW_test).abs().max().item()
        assert torch.allclose(
            W.grad, dW_test, atol = atol, rtol = rtol
        ), f"Grouped gemm manual backward_dW outputs mismatch: {diff:.6f}"