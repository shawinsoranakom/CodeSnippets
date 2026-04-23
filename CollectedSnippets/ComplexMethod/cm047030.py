def grouped_gemm_dW(
    X: torch.Tensor,
    dY: torch.Tensor,
    m_sizes: torch.Tensor,
    gather_indices: torch.Tensor,
    topk: int,
    BLOCK_SIZE_M: int = 32,
    BLOCK_SIZE_N: int = 32,
    BLOCK_SIZE_K: int = 32,
    permute_x: bool = False,
    permute_y: bool = False,
    use_tma_load_dy: bool = False,
    use_tma_load_x: bool = False,
    use_tma_store: bool = False,
    fuse_mul_pre: bool = False,
    fuse_mul_post: bool = False,
    num_warps: int = 4,
    num_stages: int = 2,
    flatten: bool = True,
    autotune: bool = False,
    debug: bool = False,
) -> torch.Tensor:
    """
    X: (M, K) hidden states where M is the num_tokens if `permute_x` is True, otherwise `total_tokens` where `total_tokens = num_tokens * topk`.
    dY: (M, N)
    topk: number of experts to choose per token.
    m_sizes: tokens assigned to each expert which correspond to the size of M in the respective GEMMs in the grouped GEMM.
    gather_indices: (total_tokens,) indices of tokens assigned to each expert.  E.g., slicing gather_indices by cumsum of m_sizes gives the indices of tokens assigned to each expert.
    permute_x: whether X was permuted on load in the forward pass, typically only used for the first grouped GEMM in an MoE MLP to group tokens by expert.
    - for the first grouped GEMM, we permuted on load -> X was [num_tokens, K] and stored y in expert grouped order [num_tokens * topk, K]
    - in the backwards pass, we need to permute on load of X while loading dy in contiguous (expert grouped) order
    - since we are writing out dW, there is no need to permute on store
    permute_y: whether the output was permuted on store in the forward pass, typically only used for the second grouped GEMM in an MoE MLP to restore to the original token order.
    - for the second grouped GEMM, we permuted on store -> y was permuted from expert grouped order to token order while X was loaded in expert grouped order since it was the output of the first grouped GEMM
    - in the backwards pass, we need to permute on load of dy to get from token order to expert grouped order to match the order of X
    - since we are writing out dW, there is no need to permute on store
    use_tma_load_dy: use TMA for loading dy. use_tma_load_dy is incompatible with permute_y.  TODO: add TMA gather / scatter support for Blackwell+ which will enable permute_y and use_tma_load_dy.
    use_tma_load_x: use TMA for loading x. use_tma_load_x is incompatible with permute_x.  TODO: add TMA gather / scatter support for Blackwell+ which will enable permute_x and use_tma_load_x.
    use_tma_store: use TMA for storing dW.  If TMA supported, this should always be enabled as it is faster than global memory store.
    """
    assert not fuse_mul_pre, "fuse_mul_pre not supported"
    assert not fuse_mul_post, "fuse_mul_post not supported"
    NUM_SMS = (
        torch.cuda.get_device_properties("cuda").multi_processor_count
        if not debug
        else 1
    )
    X = X.view(-1, X.shape[-1]).contiguous()
    dY = dY.contiguous()
    m_sizes = m_sizes.contiguous()

    # Preconditions
    assert not (permute_x and permute_y), "Cannot permute both X and Y"
    assert not (permute_y and use_tma_load_dy), "Cannot use both TMA load and permute_y"
    assert not (permute_x and use_tma_load_x), "Cannot use both TMA load and permute_x"

    use_tma = use_tma_load_dy or use_tma_load_x or use_tma_store
    if not supports_tma() and use_tma:
        warnings.warn("TMA not supported, tma_load will be set to False")
        use_tma_load_x = False
        use_tma_load_dy = False
        use_tma_store = False

    if use_tma or autotune:
        # Respect global persistent allocator if set
        if _HAS_SET_ALLOCATOR and not getattr(triton, "_unsloth_allocator_set", False):

            def alloc_fn(size: int, alignment: int, stream: int):
                return torch.empty(size, device = "cuda", dtype = torch.int8)

            triton.set_allocator(alloc_fn)

    if permute_x or permute_y:
        assert gather_indices is not None
        assert gather_indices.is_contiguous()
        assert gather_indices.device.type == "cuda"
        assert gather_indices.ndim == 1
        total_tokens = gather_indices.shape[0]
        num_tokens = total_tokens // topk
        if permute_x:
            assert X.shape[0] == num_tokens
        else:
            assert X.shape[0] == total_tokens
    else:
        total_tokens = X.shape[0]
        num_tokens = total_tokens // topk

    num_experts = m_sizes.shape[0]
    # Get dimensions
    _, K = X.shape
    M_grad, N = dY.shape

    assert M_grad == total_tokens, f"dY M ({M_grad}) != total_tokens ({total_tokens})"

    dW = torch.zeros((num_experts, N, K), device = X.device, dtype = X.dtype)

    if not autotune:
        # BLOCK_SIZE_N = min(N, BLOCK_SIZE_N)
        # BLOCK_SIZE_K = min(K, BLOCK_SIZE_K)
        pass

    def grid(META):
        return (NUM_SMS,)

    if debug:
        print(
            f"DEBUG::GROUPED_GEMM_DW_TMA {num_experts = } {N = } {K = } {BLOCK_SIZE_M = } {BLOCK_SIZE_N = } {BLOCK_SIZE_K = } {NUM_SMS = }"
        )

        print(f"DEBUG::GROUPED_GEMM_DW_TMA {m_sizes.tolist() = }")
        print(f"DEBUG::GROUPED_GEMM_DW_TMA {gather_indices.tolist() = }")
        m_start = 0
        for i in range(num_experts):
            expert_token_idx = gather_indices[m_start : m_start + m_sizes[i]]
            t_start = 0
            while t_start < m_sizes[i]:
                token_idx = expert_token_idx[t_start : t_start + BLOCK_SIZE_M]
                if permute_x:
                    token_idx = token_idx // topk
                print(
                    f"DEBUG::GROUPED_GEMM_DW_TMA Token expert {i} indices: {token_idx.tolist()}"
                )
                t_start += BLOCK_SIZE_M

            m_start += m_sizes[i]

    kernel_args = {
        # Inputs
        "x_ptr": X,
        "dY_ptr": dY,
        "m_sizes_ptr": m_sizes,
        "gather_indices_ptr": gather_indices,
        # Output
        "dW_ptr": dW,
        # Problem sizes
        "NUM_TOKENS": num_tokens,
        "TOPK": topk,
        "NUM_EXPERTS": num_experts,
        "N": N,
        "K": K,
        "NUM_SMS": NUM_SMS,
        # Gather / Scatter
        "PERMUTE_X": permute_x,
        "PERMUTE_Y": permute_y,
        # Loop pipelining
        "FLATTEN": flatten,
    }

    if not autotune:
        kernel_args.update(
            {
                "BLOCK_SIZE_M": BLOCK_SIZE_M,
                "BLOCK_SIZE_N": BLOCK_SIZE_N,
                "BLOCK_SIZE_K": BLOCK_SIZE_K,
                "USE_TMA_LOAD_dY": use_tma_load_dy,
                "USE_TMA_LOAD_X": use_tma_load_x,
                "USE_TMA_STORE": use_tma_store,
                "num_warps": num_warps,
                "num_stages": num_stages,
            }
        )

    kernel = _autotuned_grouped_gemm_dW_kernel if autotune else _grouped_gemm_dW_kernel

    is_fake = _is_tracing(X, dY)
    if not is_fake:
        compiled_kernel: triton.compiler.CompiledKernel = kernel[grid](**kernel_args)

        if autotune:
            log_kernel_info(compiled_kernel, kernel.best_config)
        else:
            log_kernel_info(compiled_kernel)

    return dW