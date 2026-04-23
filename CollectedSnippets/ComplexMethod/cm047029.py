def grouped_gemm_dX(
    dY: torch.Tensor,
    W: torch.Tensor,
    gather_indices: torch.Tensor,
    m_sizes: torch.Tensor,
    topk: int,
    BLOCK_SIZE_M: int = 32,
    BLOCK_SIZE_N: int = 32,
    BLOCK_SIZE_K: int = 32,
    debug: bool = False,
    permute_x: bool = False,
    permute_y: bool = False,
    use_tma_load_w: bool = False,
    use_tma_load_dy: bool = False,
    use_tma_store: bool = False,
    num_warps: int = 4,
    num_stages: int = 2,
    flatten: bool = True,
    fuse_mul_pre: bool = False,
    fuse_mul_post: bool = False,
    autotune: bool = False,
) -> torch.Tensor:
    """
    dX backward kernel
    grad_output: (M, N)
    gather_indices: (total_tokens,), indices of tokens assigned to each expert.  E.g., slicing gather_indices by cumsum of m_sizes gives the indices of tokens assigned to each expert.
    m_sizes: tokens assigned to each expert which correspond to the size of M in the respective GEMMs in the grouped GEMM.
    topk: number of experts chosen per token.
    `permute_x`: whether X was permuted on load in the forward pass, typically only used for the first grouped GEMM in an MoE MLP to group tokens by expert.
    - In the forward pass, if we permuted X on load, we need to permute store in the backward pass
    - Shapes
        - the forward pass input X shape is [NUM_TOKENS, K], reduce across K, output y is [NUM_TOKENS * TOPK, K]
        - the backward pass input dy shape is [NUM_TOKENS * TOPK, N], reduce across N, output dX is [NUM_TOKENS * TOPK, K]
    - Note that in the backward pass, the output size is still [NUM_TOKENS * TOPK, K] since we still need to accumulate gradients for each expert chosen by the token in a post-processing step.
    `permute_y`: whether the output was permuted on store in the forward pass, typically only used for the second grouped GEMM in an MoE MLP to restore to the original token order.
    - In the forward pass, if we permuted output on store (e.g., in the second grouped GEMM in fused MoE MLP), we need to permute on load to get from token order to expert grouped order
    - We still store in contiguous order since we are writing out dX which will be the input to the backwards pass of the first grouped GEMM
    `fuse_mul_{pre,post}`: always set to False since this should only be used for inference.
    use_tma_load_dy: use TMA for loading dy. use_tma_load_dy is incompatible with permute_y.  TODO: add TMA gather / scatter support for Blackwell+ which will enable permute_y and use_tma_load_dy.
    use_tma_load_w: use TMA for loading weights.  If TMA supported, this should always be enabled as it is faster than global memory load.
    use_tma_store: use TMA for storing dX.  Incompatible with permute_x.  TODO: add TMA gather / scatter support for Blackwell+ which will enable permute_x and use_tma_store.
    """
    assert (
        not fuse_mul_pre
    ), "fuse_mul_pre should only be used for inference, not for training"
    assert (
        not fuse_mul_post
    ), "fuse_mul_post should only be used for inference, not for training"
    assert dY.is_contiguous()
    assert W.is_contiguous()
    assert m_sizes.is_contiguous()
    assert m_sizes.ndim == 1

    # Preconditions
    assert not (permute_x and permute_y), "Cannot permute both X and Y"
    # Note that this is flipped from the forward pass
    # If we permuted y in the forward, we need to permute on load in the backward
    assert not (permute_y and use_tma_load_dy), "Cannot use both TMA load and permute_y"
    assert not (permute_x and use_tma_store), "Cannot use both TMA store and permute_x"

    use_tma = use_tma_load_dy or use_tma_load_w or use_tma_store
    if not supports_tma() and use_tma:
        warnings.warn("TMA not supported, tma_load will be set to False")
        use_tma_load_w = False
        use_tma_load_dy = False
        use_tma_store = False

    if use_tma or autotune:
        # Respect global persistent allocator if set
        if _HAS_SET_ALLOCATOR and not getattr(triton, "_unsloth_allocator_set", False):

            def alloc_fn(size: int, alignment: int, stream: int):
                # print(f"DEBUG::GROUPED_GEMM alloc_fn {size=} {alignment=} {stream=}")
                return torch.empty(size, device = "cuda", dtype = torch.int8)

            triton.set_allocator(alloc_fn)

    if W.ndim == 3:
        num_experts = W.shape[0]
        N = W.shape[1]
    else:
        num_experts = m_sizes.shape[0]
        N = W.shape[0] // num_experts

    dY = dY.view(-1, dY.shape[-1])
    W = W.view(-1, W.shape[-1])

    M_total, N_grad = dY.shape
    N_total, K = W.shape
    # N = N_total // num_experts
    assert N_grad == N, f"Grad_output N ({N_grad}) must match weight N ({N})"

    assert (
        M_total % topk == 0
    ), f"M_total ({M_total}) must be divisible by topk ({topk})"
    num_tokens = M_total // topk

    total_tokens = gather_indices.shape[0]
    assert (
        total_tokens == M_total
    ), f"Total tokens ({total_tokens}) must match M_total ({M_total})"

    # Note that the output shape is [NUM_TOKENS * TOPK, K] even when `permute_x` is True since we need to accumulate gradients across all experts chosen by the token.
    # This will be done in a post-processing step reduction step.
    output_shape = (total_tokens, K)
    dX = torch.zeros(output_shape, device = dY.device, dtype = dY.dtype)

    NUM_SMS = torch.cuda.get_device_properties(
        "cuda"
    ).multi_processor_count  # if not debug else 1

    def grid(META):
        return (NUM_SMS,)

    if not autotune:
        # BLOCK_SIZE_N = min(N_grad, BLOCK_SIZE_N)
        # BLOCK_SIZE_K = min(K, BLOCK_SIZE_K)
        pass

    if debug:
        print(
            f"DEBUG::GROUPED_GEMM {num_tokens = } {topk = } {output_shape = } {num_experts = } {N = } {K = } {BLOCK_SIZE_M = } {BLOCK_SIZE_N = } {BLOCK_SIZE_K = } {NUM_SMS = }"
        )
        print(f"DEBUG::GROUPED_GEMM {m_sizes.tolist()}")

    kernel_args = {
        # Inputs
        "dY_ptr": dY,
        "w_ptr": W,
        "gather_indices_ptr": gather_indices,
        "m_sizes_ptr": m_sizes,
        # Output
        "dX_ptr": dX,
        # Problem sizes
        "NUM_EXPERTS": num_experts,
        "NUM_TOKENS": num_tokens,
        "TOPK": topk,
        "N": N,
        "K": K,
        "NUM_SMS": NUM_SMS,
        # Gather / Scatter
        "PERMUTE_X": permute_x,
        "PERMUTE_Y": permute_y,
        "FLATTEN": flatten,
    }
    if not autotune:
        kernel_args.update(
            {
                "BLOCK_SIZE_M": BLOCK_SIZE_M,
                "BLOCK_SIZE_N": BLOCK_SIZE_N,
                "BLOCK_SIZE_K": BLOCK_SIZE_K,
                "num_warps": num_warps,
                "num_stages": num_stages,
                "USE_TMA_LOAD_dY": use_tma_load_dy,
                "USE_TMA_LOAD_W": use_tma_load_w,
                "USE_TMA_STORE": use_tma_store,
            }
        )
    kernel = _autotuned_grouped_gemm_dX_kernel if autotune else _grouped_gemm_dX_kernel

    is_fake = _is_tracing(dY, W)
    if not is_fake:
        compiled_kernel: triton.compiler.CompiledKernel = kernel[grid](**kernel_args)

        if autotune:
            log_kernel_info(compiled_kernel, kernel.best_config)
        else:
            log_kernel_info(compiled_kernel)
    return dX