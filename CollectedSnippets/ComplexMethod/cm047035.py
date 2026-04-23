def _grouped_gemm_dX_kernel(
    dY_ptr,  # [M_total, N]
    w_ptr,  # [E, N, K]
    dX_ptr,  # [M_total, K]
    gather_indices_ptr,
    m_sizes_ptr,
    # problem sizes
    NUM_EXPERTS: tl.constexpr,
    NUM_TOKENS,
    TOPK: tl.constexpr,
    N: tl.constexpr,
    K: tl.constexpr,
    NUM_SMS,
    # Tuning parameters
    BLOCK_SIZE_M: tl.constexpr,
    BLOCK_SIZE_N: tl.constexpr,
    BLOCK_SIZE_K: tl.constexpr,
    PERMUTE_X: tl.constexpr = False,
    PERMUTE_Y: tl.constexpr = False,
    USE_TMA_LOAD_W: tl.constexpr = False,
    USE_TMA_LOAD_dY: tl.constexpr = False,
    USE_TMA_STORE: tl.constexpr = False,
    FLATTEN: tl.constexpr = True,
) -> None:
    TOTAL_TOKENS = NUM_TOKENS * TOPK
    output_dtype = dX_ptr.dtype.element_ty

    tidx = tl.program_id(0)
    # This removes the need for predication along N in the GEMM main loop
    tl.static_assert(N % BLOCK_SIZE_N == 0, "N must be divisible by BLOCK_SIZE_N")
    tl.static_assert(K % BLOCK_SIZE_K == 0, "K must be divisible by BLOCK_SIZE_K")

    # Create TMA descriptors for loading sorted tokens
    # When using TMA load, we don't permute_x, so shape should be [TOTAL_TOKENS, K]
    # Also, we are defining a single global descriptor with single block shape
    # Need to check that this does not result in errors when crossing expert boundaries
    if USE_TMA_LOAD_dY:
        dY_desc = tl.make_tensor_descriptor(
            dY_ptr,
            shape = [TOTAL_TOKENS, N],
            strides = [N, 1],
            block_shape = [BLOCK_SIZE_M, BLOCK_SIZE_N],
        )

    if USE_TMA_LOAD_W:
        expert_stride = N * K
        w_desc = tl.make_tensor_descriptor(
            w_ptr,
            shape = [NUM_EXPERTS, N, K],
            strides = [expert_stride, K, 1],
            block_shape = [1, BLOCK_SIZE_N, BLOCK_SIZE_K],
        )

    m_end = 0
    processed_tiles = 0
    m_block_range = tl.arange(0, BLOCK_SIZE_M)
    n_block_range = tl.arange(0, BLOCK_SIZE_N)
    k_block_range = tl.arange(0, BLOCK_SIZE_K)

    for expert_idx in range(NUM_EXPERTS, flatten = FLATTEN):
        m_start = m_end
        m_size = tl.load(m_sizes_ptr + expert_idx).to(tl.int32)
        m_end = m_start + m_size

        if m_size > 0:
            # Advance n offset to the weights for that respective expert
            n_start = expert_idx * N
            # N_start_offset = g.to(tl.int64) * N
            # tiles for this group's GEMM
            num_m_tiles = tl.cdiv(m_size, BLOCK_SIZE_M)
            num_k_tiles = tl.cdiv(K, BLOCK_SIZE_K)
            num_tiles_per_expert = num_m_tiles * num_k_tiles

            if USE_TMA_STORE:
                # Need to define descript within loop to predicate store along M
                tl.static_assert(
                    K % BLOCK_SIZE_K == 0, "K must be divisible by BLOCK_SIZE_K"
                )
                dX_desc = tl.make_tensor_descriptor(
                    dX_ptr,
                    shape = [m_end, K],
                    strides = [K, 1],
                    block_shape = [BLOCK_SIZE_M, BLOCK_SIZE_K],
                )

            # Lower bound and upper bound are defined relative to the total tiles processed so far
            # This ensures that we are only processing tiles for the current expert group AND
            # we never exceed the total number of tiles for all expert groups
            while tidx >= processed_tiles and tidx < (
                processed_tiles + num_tiles_per_expert
            ):
                group_index = tidx - processed_tiles

                # Output tile for this thread block for this expert group
                tile_m_idx = group_index % num_m_tiles
                tile_k_idx = group_index // num_m_tiles

                if PERMUTE_X or PERMUTE_Y:
                    # These will be used for loading and storing in permuted order
                    gather_offsets = tile_m_idx * BLOCK_SIZE_M + m_block_range
                    # indices_to_gather = m_start + gather_offsets
                    indices_to_gather = m_start + tl.max_contiguous(
                        tl.multiple_of(gather_offsets % m_size, BLOCK_SIZE_M),
                        BLOCK_SIZE_M,
                    )
                    expert_token_idx = tl.load(
                        gather_indices_ptr + indices_to_gather,
                        mask = indices_to_gather < TOTAL_TOKENS,
                    )
                    expert_token_offsets = expert_token_idx[:, None]

                    # Masks for permuted load and store
                    row_mask = gather_offsets < m_size
                    row_mask = row_mask[:, None]

                    # We only take into account the following two cases: (PERMUTE_X and NOT PERMUTE_Y) and (NOT PERMUTE_X and PERMUTE_Y)
                    # Hence, we can make the following simplifying assumptions when loading and storing
                    # Note the different strides between the two cases: the offsets for loading and storing are flipped and the strides must also be adjusted

                    if PERMUTE_X:
                        # Case where we permuted on load in the forward pass (typically first grouped GEMM in MoE MLP)
                        load_a_idx = (
                            indices_to_gather[:, None] * N
                        )  # Load in contiguous (expert grouped) order
                        store_idx = (
                            expert_token_offsets * K
                        )  # Permute on store from expert -> token order
                    else:
                        # Case where we permuted on store in the forward pass (typically second grouped GEMM in MoE MLP)
                        load_a_idx = (
                            expert_token_offsets * N
                        )  # Permute on load from token -> expert order
                        store_idx = (
                            indices_to_gather[:, None] * K
                        )  # Store in contiguous order
                else:
                    # # Position in full matrix - needed for TMA
                    # m_offset = (M_start + (tile_m_idx * BLOCK_SIZE_M)).to(tl.int32)
                    # k_offset = (tile_k_idx * BLOCK_SIZE_K).to(tl.int32)
                    # Offsets *relative* to the *current* expert -- m_start will then advance to this expert's start token
                    offs_am = tile_m_idx * BLOCK_SIZE_M + m_block_range

                    # [M, N] @ [N, K] -> [M, K] => Stride for A is N, stride for B is K
                    # We need two additional offsets:
                    # 1. For A, m_start to advance to this expert's start token
                    # 2. For B, n_start to advance to this expert's weights since we are passing in an [E, N, K] weight matrix
                    row_offsets_a = m_start + offs_am[:, None]
                    load_a_idx = row_offsets_a * N
                    store_idx = row_offsets_a * K
                    row_mask = offs_am[:, None] < m_size

                if not USE_TMA_LOAD_dY:
                    dY_ptrs = dY_ptr + load_a_idx + n_block_range[None, :]

                offs_bk = tile_k_idx * BLOCK_SIZE_K + k_block_range
                if not USE_TMA_LOAD_W:
                    row_offsets_b = n_start + n_block_range
                    # offs_bn = n_start + n_block_range
                    # row_offsets_b = tl.max_contiguous(tl.multiple_of(offs_bn, BLOCK_SIZE_N), BLOCK_SIZE_N)
                    w_ptrs = w_ptr + row_offsets_b[:, None] * K + offs_bk[None, :]

                # TODO: check whether predication along K is needed since we checked that K is divisible by BLOCK_SIZE_K in the forward kernel
                # col_mask = offs_bk[None, :] < K
                store_mask = row_mask  # & col_mask

                accumulator = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_K), dtype = tl.float32)

                # GEMM main loop
                for n_offset in range(0, N, BLOCK_SIZE_N):
                    # dY block [M, N]
                    if not USE_TMA_LOAD_dY:
                        dY = tl.load(dY_ptrs, mask = row_mask)
                    else:
                        dY = dY_desc.load(
                            [m_start + tile_m_idx * BLOCK_SIZE_M, n_offset]
                        )

                    if not USE_TMA_LOAD_W:
                        w = tl.load(w_ptrs)  # , mask=col_mask)
                    else:
                        w = w_desc.load(
                            [expert_idx, n_offset, tile_k_idx * BLOCK_SIZE_K]
                        )
                        w = tl.reshape(w, (BLOCK_SIZE_N, BLOCK_SIZE_K))
                    # TODO: check if predication along K is needed since we checked that K is divisible by BLOCK_SIZE_K in the forward kernel

                    # [M, N] @ [N, K] -> [M, K]
                    dY = dY.to(w.dtype)
                    accumulator += tl.dot(dY, w)  # NOTE: no transpose of b

                    # Advance A along contiguous dimension
                    if not USE_TMA_LOAD_dY:
                        dY_ptrs += BLOCK_SIZE_N
                    # Note we are no longer advancing B along contiguous dimension since weights are arranged as [N, K]
                    # Instead, we need to stride by K to advance to the [N_BLOCK_SIZE, K_BLOCK_SIZE] tile
                    if not USE_TMA_LOAD_W:
                        w_ptrs += BLOCK_SIZE_N * K

                dX = accumulator.to(output_dtype)

                # Writing out a BLOCK_M x BLOCK_K tile, so we need to stride by K
                if USE_TMA_STORE:
                    offset_m = tile_m_idx * BLOCK_SIZE_M  # .to(tl.int32)
                    offset_k = tile_k_idx * BLOCK_SIZE_K  # .to(tl.int32)
                    dX_desc.store([m_start + offset_m, offset_k], dX)
                else:
                    tl.store(
                        dX_ptr + store_idx + offs_bk[None, :],
                        dX,
                        mask = store_mask,
                    )

                # Move to the next tile within this expert group
                tidx += NUM_SMS

            # Update the total tiles count for the next expert group
            processed_tiles += num_tiles_per_expert