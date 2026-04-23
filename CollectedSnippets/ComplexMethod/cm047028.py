def grouped_gemm_forward(
    X: torch.Tensor,
    W: torch.Tensor,
    topk: int,
    m_sizes: torch.Tensor,
    gather_indices: torch.Tensor = None,
    topk_weights: torch.Tensor = None,
    # Fusions
    permute_x: bool = False,
    permute_y: bool = False,
    fuse_mul_post: bool = False,
    # Autotuning - manual kernel params will be ignored if autotune is True
    autotune: bool = False,
    # Kernel tuning params if not autotuning -- NOTE: these params need to be tuned, otherwise performance will be poor
    BLOCK_SIZE_M: int = 32,
    BLOCK_SIZE_N: int = 32,
    BLOCK_SIZE_K: int = 32,
    num_warps: int = 4,
    num_stages: int = 2,
    use_tma_load_w: bool = False,
    use_tma_load_x: bool = False,
    use_tma_store: bool = False,
    # software pipelining -- set to True for now, won't impact until loop is re-written
    flatten: bool = True,
    # debugging
    debug: bool = False,
) -> torch.Tensor:
    """
    Grouped GEMM forward pass for MoE MLPs.

    The implementation offers a number of fusions specific to MoE:
    - `permute_x`: fuse the permutation of hidden states from token order (original order) to grouped expert order, typically only needed for the first grouped GEMM in an MoE MLP.
        - When `permute_x` is True, `X` is expected to be of shape (num_tokens, K).
        - When `permute_x` is False, `X` is expected to be of shape (total_tokens, K) where `total_tokens = num_tokens * topk` AND already permuted to grouped expert order, i.e., hidden states are sorted such that tokens assigned to each expert are contiguous.
    - `permute_y`: fused the permutation of the output from expert grouped order back to original token order, typically only needed for the second grouped GEMM in an MoE MLP.
    - `fuse_mul_pre`: fuse the multiplication of the routed input with topk_weights, only done in the first grouped GEMM in an MoE MLP as for Llama4.  Do not use, since results in performance regression as it interrupts the GEMM mainloop.
    - `fuse_mul_post`: fuse the multiplication of the routed output with topk_weights, used only when `permute_y` is True. NOTE: this should only be used when using this kernel for inference, not for training.

    X: (M, K) hidden states where M is the num_tokens if `permute_x` is True, otherwise `total_tokens` where `total_tokens = num_tokens * topk`.
    W: (E, N, K) expert weights, where E is number of experts, N in the intermediate (output) dim, and K is the reduction dim
    m_sizes: tokens assigned to each expert which correspond to the size of M in the respective GEMMs in the grouped GEMM.
    gather_indices: (total_tokens,) indices of tokens assigned to each expert.  E.g., slicing gather_indices by cumsum of m_sizes gives the indices of tokens assigned to each expert.
    topk_weights: (total_tokens,) weights to multiply routed output by in expert MLP calculation, used only when `fuse_mul_post` is True (see note on `fuse_mul_post`).
    use_fast_accum: currently unused; trade off faster accumulation dtype in GEMM for less precision.
    use_tma_load_x: use TMA for loading activations, incompatible with permute_x.  TODO: add TMA gather / scatter support for Blackwell+.
    use_tma_load_w: use TMA for loading weights.  If TMA supported, this should always be enabled as it is faster than global memory load.
    use_tma_store: use TMA for storing output, incompatible with permute_y.  TODO: add TMA scatter support for Blackwell+.

    Returns:
        y: (total_tokens, N) output of grouped GEMM
    """

    assert X.device.type == "cuda", "X and W must be on CUDA"
    assert m_sizes.device.type == "cuda", "m_sizes must be on CUDA"

    X = X.contiguous()
    W = W.contiguous()
    m_sizes = m_sizes.contiguous()

    # Preconditions
    assert not (permute_x and permute_y), "Cannot permute both X and Y"
    assert not (permute_y and use_tma_store), "Cannot use both TMA store and permute_y"

    if use_tma_load_x:
        # TMA load for activations, TMA gather only supported on Blackwell+
        assert not permute_x, "Cannot use both use_tma_load_x and permute_x"

    use_tma = use_tma_load_w or use_tma_load_x or use_tma_store
    if not supports_tma() and use_tma:
        warnings.warn("TMA not supported, tma_load will be set to False")
        use_tma_load_w = False
        use_tma_load_x = False
        use_tma_store = False

    if use_tma or autotune:
        # Respect global persistent allocator if set
        if _HAS_SET_ALLOCATOR and not getattr(triton, "_unsloth_allocator_set", False):

            def alloc_fn(size: int, alignment: int, stream: int):
                return torch.empty(size, device = "cuda", dtype = torch.int8)

            triton.set_allocator(alloc_fn)

    if W.ndim == 3:
        num_experts = W.shape[0]
        N = W.shape[1]
        # K = W.shape[2]
    else:
        num_experts = m_sizes.shape[0]
        N = W.shape[0] // num_experts

    X = X.view(-1, X.shape[-1])
    W = W.view(-1, W.shape[-1])

    if permute_x or permute_y:
        assert (
            gather_indices is not None
        ), "gather_indices must be provided when permute_x or permute_y is True"
        assert gather_indices.is_contiguous()
        assert gather_indices.device.type == "cuda"
        assert gather_indices.ndim == 1
        total_tokens = gather_indices.shape[0]
        num_tokens = total_tokens // topk
        if permute_x:
            assert (
                X.shape[0] == num_tokens
            ), f"X.shape[0] ({X.shape[0]}) must match num_tokens ({num_tokens})"
        else:
            assert (
                X.shape[0] == total_tokens
            ), f"X.shape[0] ({X.shape[0]}) must match total_tokens ({total_tokens})"
    else:
        total_tokens = X.shape[0]
        num_tokens = total_tokens // topk

    _, K = X.shape
    assert K == W.shape[1], f"K ({K}) must match W.shape[1] ({W.shape[1]})"

    if fuse_mul_post:
        global _FUSED_MUL_WARN
        if not _FUSED_MUL_WARN:
            warnings.warn(
                "fused_mul should only be used for inference, not for training"
            )
            _FUSED_MUL_WARN = True
        assert permute_y, "FUSE_MUL requires PERMUTE_Y"
        assert topk_weights is not None
        assert topk_weights.numel() == total_tokens
        assert topk_weights.device.type == "cuda"
        assert topk_weights.is_contiguous()
        topk_weights = topk_weights.view(-1)
        if debug:
            print(
                f"DEBUG::GROUPED_GEMM {topk_weights.tolist()} {gather_indices.tolist()}"
            )

    y = torch.empty((total_tokens, N), device = X.device, dtype = X.dtype)
    # if total_tokens == 0 or N == 0:
    #     return y

    NUM_SMS = torch.cuda.get_device_properties("cuda").multi_processor_count

    def grid(META):
        return (NUM_SMS,)

    if not autotune:
        # BLOCK_SIZE_K = min(K, BLOCK_SIZE_K)
        # BLOCK_SIZE_N = min(N, BLOCK_SIZE_N)
        pass

    if debug:
        print(
            f"DEBUG::GROUPED_GEMM {num_tokens = } {topk = } {num_experts = } {N = } {K = } {BLOCK_SIZE_M = } {BLOCK_SIZE_N = } {BLOCK_SIZE_K = } {permute_x = }"
        )
        print(
            f"DEBUG::GROUPED_GEMM {m_sizes.tolist()} {(gather_indices // topk).tolist()}"
        )

    kernel_args = {
        # Inputs
        "x_ptr": X,
        "w_ptr": W,
        "m_sizes_ptr": m_sizes,
        "gather_indices_ptr": gather_indices,
        "topk_weights_ptr": topk_weights,
        # Output
        "y_ptr": y,
        # Problem shapes
        "NUM_TOKENS": num_tokens,
        "NUM_EXPERTS": num_experts,
        "TOPK": topk,
        "N": N,
        "K": K,
        "NUM_SMS": NUM_SMS,
        # Gather / Scatter
        "PERMUTE_X": permute_x,
        "PERMUTE_Y": permute_y,
        # TopK weight merging
        "FUSE_MUL_POST": fuse_mul_post,
        # Loop pipelining
        "FLATTEN": flatten,
    }
    if not autotune:
        kernel_args.update(
            {
                "USE_TMA_LOAD_W": use_tma_load_w,
                "USE_TMA_LOAD_X": use_tma_load_x,
                "USE_TMA_STORE": use_tma_store,
                "BLOCK_SIZE_M": BLOCK_SIZE_M,
                "BLOCK_SIZE_N": BLOCK_SIZE_N,
                "BLOCK_SIZE_K": BLOCK_SIZE_K,
                "num_warps": num_warps,
                "num_stages": num_stages,
            }
        )

    kernel = (
        _autotuned_grouped_gemm_forward_kernel
        if autotune
        else _grouped_gemm_forward_kernel
    )

    is_fake = _is_tracing(X, W)
    if not is_fake:
        compiled_kernel: triton.compiler.CompiledKernel = kernel[grid](**kernel_args)
        if autotune:
            log_kernel_info(compiled_kernel, kernel.best_config)
        else:
            log_kernel_info(compiled_kernel)

    return y