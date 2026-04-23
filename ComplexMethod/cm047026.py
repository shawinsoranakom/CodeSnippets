def _test_grouped_gemm_backward_dX(
    data_config: DataConfig,
    model_config: ModelConfig,
    permute_x: bool = False,
    permute_y: bool = False,
    use_tma_load_dy: bool = False,
    use_tma_load_w: bool = False,
    use_tma_store: bool = False,
    use_W1: bool = True,
    autotune: bool = False,
    num_autotune_configs: int = None,
    BLOCK_SIZE_M: int = None,
    BLOCK_SIZE_N: int = None,
    BLOCK_SIZE_K: int = None,
    num_warps: int = None,
    num_stages: int = None,
    flatten: bool = True,
    allow_tma_store: bool = False,
    use_autograd: bool = False,
    fuse_mul_post: bool = False,
):
    if not check_valid_config(permute_x, permute_y, use_W1 = use_W1, is_backward = True):
        pytest.skip(
            f"Skipping test due to invalid config: {permute_x = } {permute_y = } {use_W1 = }"
        )

    if use_tma_store and not allow_tma_store:
        pytest.skip("TMA store needs to be debugged due to non-deterministic behavior")

    if (
        autotune
        and model_config.intermediate_size <= 128
        and model_config.hidden_size <= 128
    ):
        pytest.skip("Skipping autotuning for small model configs")

    # Prevent OOM for large intermediate sizes
    if model_config.intermediate_size > 2048:
        model_config.intermediate_size = 1024
    if model_config.hidden_size > 2048:
        model_config.hidden_size = 1024

    use_W2 = not use_W1
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
    total_tokens = num_tokens * topk

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
            total_tokens,
            N,
        ), f"X.shape: {X.shape}, total_tokens: {total_tokens}, N: {N}"

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

    # Need to retain grad otherwise grad is not propagated
    X.retain_grad()
    W.retain_grad()
    Xperm.retain_grad()

    assert Xperm.shape == (total_tokens, K) if use_W1 else (total_tokens, N)

    output_shape = (total_tokens, 2 * N) if use_W1 else (total_tokens, K)
    ref_output = torch_grouped_gemm(X = Xperm, W = W, m_sizes = expert_token_counts)
    assert (
        ref_output.shape == output_shape
    ), f"ref_output.shape: {ref_output.shape}, output_shape: {output_shape}"

    if permute_y:
        ref_output = unpermute(ref_output, gather_indices)

    grad_output = torch.randn_like(ref_output)
    ref_output.backward(grad_output)

    assert X.grad is not None
    assert W.grad is not None

    ref_grad = Xperm.grad

    if autotune:
        # No need to run all configs for autotuning
        from grouped_gemm.kernels.backward import _autotuned_grouped_gemm_dX_kernel

        if num_autotune_configs is not None:
            _autotuned_grouped_gemm_dX_kernel.configs = (
                _autotuned_grouped_gemm_dX_kernel.configs[:num_autotune_configs]
            )

    if use_autograd:
        from grouped_gemm.interface import grouped_gemm

        if not autotune:
            kernel_config_fwd = KernelConfigForward()
            kernel_config_bwd_dX = KernelConfigBackward_dX(
                use_tma_load_dy = use_tma_load_dy,
                use_tma_load_w = use_tma_load_w,
                use_tma_store = use_tma_store,
                BLOCK_SIZE_M = BLOCK_SIZE_M,
                BLOCK_SIZE_N = BLOCK_SIZE_N,
                BLOCK_SIZE_K = BLOCK_SIZE_K,
                num_warps = num_warps,
                num_stages = num_stages,
            )
            kernel_config_bwd_dW = KernelConfigBackward_dW()
        else:
            from grouped_gemm.kernels.backward import (
                _autotuned_grouped_gemm_dW_kernel,
                _autotuned_grouped_gemm_dX_kernel,
            )
            from grouped_gemm.kernels.forward import (
                _autotuned_grouped_gemm_forward_kernel,
            )

            if num_autotune_configs is not None:
                _autotuned_grouped_gemm_dX_kernel.configs = (
                    _autotuned_grouped_gemm_dX_kernel.configs[:num_autotune_configs]
                )
                _autotuned_grouped_gemm_forward_kernel.configs = (
                    _autotuned_grouped_gemm_forward_kernel.configs[
                        :num_autotune_configs
                    ]
                )

            kernel_config_fwd = None
            kernel_config_bwd_dX = None
        X_ = (
            X.detach().clone().requires_grad_(True)
            if permute_x
            else Xperm.detach().clone().requires_grad_(True)
        )
        test_output = grouped_gemm(
            X = X_,
            W = W_test,
            m_sizes = expert_token_counts,
            gather_indices = gather_indices,
            topk = topk,
            permute_x = permute_x,
            permute_y = permute_y,
            autotune = autotune,
            kernel_config_fwd = kernel_config_fwd,
            kernel_config_bwd_dX = kernel_config_bwd_dX,
            is_first_gemm = use_W1,
            dX_only = True,
        )
        assert (
            test_output.shape == ref_output.shape
        ), f"test_output.shape: {test_output.shape}, ref_output.shape: {ref_output.shape}"
        assert torch.allclose(
            test_output, ref_output, atol = atol, rtol = rtol
        ), f"Grouped gemm backward_dX forward outputs mismatch: {(test_output - ref_output).abs().max().item():.6f}"
        test_output.backward(grad_output)
        assert X_.grad is not None

        # NOTE:need to handle grad differenlty in this case due to errors arising to do how torch autograd handles unpermute and sum reduction
        # the grad of Xperm unpermuted and reduced across topk should match X_.grad
        # However, both will have a numerical difference with that of ref_grad
        # This is due to the fact that torch autograd handles unpermute and sum reduction differently see: https://discuss.pytorch.org/t/permute-unpermute-gradient/219557    else:
        if permute_x and use_W1:
            X_grad_unperm = unpermute(Xperm.grad, gather_indices)
            manual_grad_check = X_grad_unperm.view(num_tokens, topk, K).sum(dim = 1)
            assert (
                manual_grad_check.shape == X_.grad.shape
            ), f"manual_grad_check.shape: {manual_grad_check.shape}, X_.grad.shape: {X_.grad.shape}"
            assert torch.allclose(
                manual_grad_check, X_.grad, atol = atol, rtol = rtol
            ), f"Grouped gemm backward_dX forward outputs mismatch: {(manual_grad_check - X_.grad).abs().max().item():.6f}"
            manual_diff = (X_.grad - manual_grad_check).abs().max().item()
            autograd_diff = (X_.grad - X.grad).abs().max().item()
            print(f"manual_diff: {manual_diff:.6f}, autograd_diff: {autograd_diff:.6f}")
        else:
            assert torch.allclose(
                X_.grad, ref_grad, atol = atol, rtol = rtol
            ), f"Grouped gemm backward_dX forward outputs mismatch: {(X_.grad - ref_grad).abs().max().item():.6f}"
        return
    else:
        dX_test = grouped_gemm_dX(
            dY = grad_output,
            W = W_test,
            gather_indices = gather_indices,
            m_sizes = expert_token_counts,
            topk = topk,
            permute_x = permute_x,
            permute_y = permute_y,
            use_tma_load_w = use_tma_load_w,
            use_tma_load_dy = use_tma_load_dy,
            use_tma_store = use_tma_store,
            autotune = autotune,
            BLOCK_SIZE_M = BLOCK_SIZE_M,
            BLOCK_SIZE_N = BLOCK_SIZE_N,
            BLOCK_SIZE_K = BLOCK_SIZE_K,
            num_warps = num_warps,
            num_stages = num_stages,
            flatten = flatten,
            # debug=True,
        )

    # if permute_x and use_W1 (first grouped GEMM) then the kernel should have unpermuted the dX
    # therefore we need to unpermute the ref_grad to compare to the output of the kernel
    if permute_x and use_W1:
        ref_grad = unpermute(ref_grad, gather_indices)

    assert (
        ref_grad.shape == dX_test.shape
    ), f"Grouped gemm manual backward_dX outputs mismatch: ref_grad: {ref_grad.shape}, dX_test: {dX_test.shape}"
    diff = (ref_grad - dX_test).abs().max().item()

    assert torch.allclose(
        ref_grad, dX_test, atol = atol, rtol = rtol
    ), f"Grouped gemm manual backward_dX outputs mismatch: {diff:.6f}"

    if permute_x and use_W1:
        # Show that reduction results in diffs
        # First calculate X.grad manually by backpropping through unpermuted ref_grad
        dX_ref_check = ref_grad.view(num_tokens, topk, K).sum(dim = 1)
        # Do the same for the actual output of the kernel
        dX_test_check = dX_test.view(num_tokens, topk, K).sum(dim = 1)
        # Show diffs for each combination
        diff_ref_check = (X.grad - dX_ref_check).abs().max().item()
        diff_test_check = (X.grad - dX_test_check).abs().max().item()
        diff_check_test = (dX_ref_check - dX_test_check).abs().max().item()
        print(
            f"diff_ref_check: {diff_ref_check:.6f}, diff_test_check: {diff_test_check:.6f}, diff_check_test: {diff_check_test:.6f}"
        )