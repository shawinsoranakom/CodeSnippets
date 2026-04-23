def grouped_gemm(
    X: torch.Tensor,
    W: torch.Tensor,
    m_sizes: torch.Tensor,
    topk: int,
    gather_indices: torch.Tensor = None,
    permute_x: bool = False,
    permute_y: bool = False,
    topk_weights = None,
    fuse_mul_post = False,
    kernel_config_fwd: KernelConfigForward = None,
    kernel_config_bwd_dX: KernelConfigBackward_dX = None,
    kernel_config_bwd_dW: KernelConfigBackward_dW = None,
    autotune: bool = False,
    is_first_gemm: bool = True,
    # Only for debugging
    dX_only: bool = False,
    dW_only: bool = False,
):
    """
    Grouped GEMM for MoE MLPs.

    The implementation offers a number of fusions specific to MoE:
    - `permute_x`: fuse the permutation of hidden states from token order (original order) to grouped expert order, typically only needed for the first grouped GEMM in an MoE MLP.
        - When `permute_x` is True, `X` is expected to be of shape (num_tokens, K).
        - When `permute_x` is False, `X` is expected to be of shape (total_tokens, K) where `total_tokens = num_tokens * topk` AND already permuted to grouped expert order, i.e., hidden states are sorted such that tokens assigned to each expert are contiguous.
    - `permute_y`: fused the permutation of the output from expert grouped order back to original token order, typically only needed for the second grouped GEMM in an MoE MLP.
    - `fuse_mul`: fuse the multiplication of the routed output with topk_weights, used only when `permute_y` is True. NOTE: this should only be used when using this kernel for inference, not for training.

    X: (M, K) hidden states where M is the num_tokens if `permute_x` is True, otherwise `total_tokens` where `total_tokens = num_tokens * topk`.
    W: (E, N, K) expert weights, where E is number of experts, N in the intermediate (output) dim, and K is the reduction dim
    m_sizes: tokens assigned to each expert which correspond to the size of M in the respective GEMMs in the grouped GEMM.
    gather_indices: (total_tokens,) indices of tokens assigned to each expert.  E.g., slicing gather_indices by cumsum of m_sizes gives the indices of tokens assigned to each expert. Needed when either `permute_x` or `permute_y` is True.
    topk_weights: (total_tokens,) weights to multiply routed output by in expert MLP calculation, used only when `fuse_mul` is True (see note on `fuse_mul`).
    kernel_config_fwd: KernelConfigForward for forward pass.
    kernel_config_bwd_dX: KernelConfigBackward_dX for backward pass of dX.
    kernel_config_bwd_dW: KernelConfigBackward_dW for backward pass of dW.
    autotune: whether to autotune the kernel, if yes, kernel_config_fwd, kernel_config_bwd_dX, and kernel_config_bwd_dW will be ignored.
    is_first_gemm: whether this is the first grouped GEMM in an MoE MLP.  This is needed to check whether kernel configs are valid.  `permute_x` should only be used for first gemm; `permute_y` should only be used for second gemm.
    This will impact whether TMA can be used for loading and storing.

    """
    if not autotune:
        assert (
            kernel_config_fwd is not None
        ), "kernel_config_fwd must be provided if autotune is False"

        check_valid_config_fwd(
            permute_x,
            permute_y,
            use_tma_load_x = kernel_config_fwd.use_tma_load_x,
            use_tma_load_w = kernel_config_fwd.use_tma_load_w,
            use_tma_store = kernel_config_fwd.use_tma_store,
            fuse_mul_post = fuse_mul_post,
            is_first_gemm = is_first_gemm,
        )
        if kernel_config_bwd_dW is not None and not dX_only:
            check_valid_config_bwd_dW(
                permute_x,
                permute_y,
                use_tma_load_dY = kernel_config_bwd_dW.use_tma_load_dy,
                use_tma_load_x = kernel_config_bwd_dW.use_tma_load_x,
                use_tma_store = kernel_config_bwd_dW.use_tma_store,
                fuse_mul_post = fuse_mul_post,
                is_first_gemm = is_first_gemm,
            )
        if kernel_config_bwd_dX is not None and not dW_only:
            check_valid_config_bwd_dX(
                permute_x,
                permute_y,
                use_tma_load_dY = kernel_config_bwd_dX.use_tma_load_dy,
                use_tma_load_w = kernel_config_bwd_dX.use_tma_load_w,
                use_tma_store = kernel_config_bwd_dX.use_tma_store,
                fuse_mul_post = fuse_mul_post,
                is_first_gemm = is_first_gemm,
            )

    if permute_x or permute_y:
        assert (
            gather_indices is not None
        ), "gather_indices is required when either permute_x or permute_y is True"

    if fuse_mul_post:
        assert (
            topk_weights is not None
        ), "topk_weights is required when fuse_mul_post is True"

    X = X.view(-1, X.shape[-1])
    m_sizes = m_sizes.view(-1)
    gather_indices = gather_indices.view(-1)

    return GroupedGemm.apply(
        X,
        W,
        m_sizes,
        topk,
        gather_indices,
        permute_x,
        permute_y,
        topk_weights,
        fuse_mul_post,
        kernel_config_fwd,
        kernel_config_bwd_dX,
        kernel_config_bwd_dW,
        autotune,
        dX_only,
        dW_only,
    )