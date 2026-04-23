def _grouped_gemm_dW_kernel(
    x_ptr,
    dY_ptr,
    dW_ptr,
    m_sizes_ptr,
    gather_indices_ptr,
    # problem sizes
    NUM_TOKENS,
    TOPK: tl.constexpr,
    NUM_EXPERTS: tl.constexpr,
    N: tl.constexpr,
    K: tl.constexpr,
    NUM_SMS,
    BLOCK_SIZE_N: tl.constexpr,
    BLOCK_SIZE_K: tl.constexpr,
    BLOCK_SIZE_M: tl.constexpr,
    PERMUTE_X: tl.constexpr = False,
    PERMUTE_Y: tl.constexpr = False,
    USE_TMA_LOAD_dY: tl.constexpr = False,
    USE_TMA_LOAD_X: tl.constexpr = False,
    USE_TMA_STORE: tl.constexpr = False,
    FLATTEN: tl.constexpr = True,
    acc_dtype: tl.constexpr = tl.float32,
) -> None:
    TOTAL_TOKENS = NUM_TOKENS * TOPK
    TMA_LOAD_BOTH: tl.constexpr = USE_TMA_LOAD_X and USE_TMA_LOAD_dY

    tidx = tl.program_id(0)
    output_dtype = dW_ptr.dtype.element_ty

    if USE_TMA_LOAD_dY and not TMA_LOAD_BOTH:
        dY_desc = tl.make_tensor_descriptor(
            dY_ptr,
            shape = [TOTAL_TOKENS, N],
            strides = [N, 1],
            block_shape = [BLOCK_SIZE_M, BLOCK_SIZE_N],
        )

    if USE_TMA_LOAD_X and not TMA_LOAD_BOTH:
        x_desc = tl.make_tensor_descriptor(
            x_ptr,
            shape = [TOTAL_TOKENS, K],
            strides = [K, 1],
            block_shape = [BLOCK_SIZE_M, BLOCK_SIZE_K],
        )
    # Output tiles per expert, since each expert weight matrix is [N, K]
    num_n_tiles = tl.cdiv(N, BLOCK_SIZE_N)
    num_k_tiles = tl.cdiv(K, BLOCK_SIZE_K)
    output_tiles_per_expert = num_n_tiles * num_k_tiles

    block_range_m = tl.arange(0, BLOCK_SIZE_M)
    block_range_n = tl.arange(0, BLOCK_SIZE_N)
    block_range_k = tl.arange(0, BLOCK_SIZE_K)

    # NOTE: Important that N % BLOCK_SIZE_N == 0 and K % BLOCK_SIZE_K == 0 when using TMA store
    if USE_TMA_STORE:
        tl.static_assert(N % BLOCK_SIZE_N == 0, "N must be divisible by BLOCK_SIZE_N")
        tl.static_assert(K % BLOCK_SIZE_K == 0, "K must be divisible by BLOCK_SIZE_K")
        dW_desc = tl.make_tensor_descriptor(
            dW_ptr,
            shape = [NUM_EXPERTS, N, K],
            strides = [N * K, K, 1],
            block_shape = [1, BLOCK_SIZE_N, BLOCK_SIZE_K],
        )

    for tile_idx in range(
        tidx, output_tiles_per_expert, NUM_SMS
    ):  # , flatten=FLATTEN):
        # Output tile index
        tile_n_idx = tile_idx % num_n_tiles
        tile_k_idx = tile_idx // num_n_tiles

        # Output tile offsets
        n_offset = tile_n_idx * BLOCK_SIZE_N
        k_offset = tile_k_idx * BLOCK_SIZE_K

        # For storing
        # TODO: Check whether the k mask is needed since we statically check that K is divisible by BLOCK_SIZE_K in the forward kernel
        # ditto for n_mask
        n_mask = block_range_n + n_offset < N
        k_mask = block_range_k + k_offset < K
        nk_mask = n_mask[:, None] & k_mask[None, :]

        m_end = 0
        for expert_idx in range(NUM_EXPERTS):
            # We need to instantiate a fresh accumulator for each expert
            accumulator = tl.zeros((BLOCK_SIZE_N, BLOCK_SIZE_K), dtype = acc_dtype)

            m_start = m_end
            # Need to figure out why this cast is needed, otherwise compiler complains about mismatching types
            m_size = tl.load(m_sizes_ptr + expert_idx).to(tl.int32)
            m_end = m_start + m_size

            # NOTE: when storing the result, we need to offset by n_start since we are storing the result for this expert to the global [E, N, K] weight matrix
            n_start = expert_idx * N
            store_row_offs = n_start + n_offset + block_range_n

            if m_size > 0:
                if TMA_LOAD_BOTH:
                    dY_desc = tl.make_tensor_descriptor(
                        dY_ptr,
                        shape = [m_end, N],
                        strides = [N, 1],
                        block_shape = [BLOCK_SIZE_M, BLOCK_SIZE_N],
                    )

                    x_desc = tl.make_tensor_descriptor(
                        x_ptr,
                        shape = [m_end, K],
                        strides = [K, 1],
                        block_shape = [BLOCK_SIZE_M, BLOCK_SIZE_K],
                    )

                for tile_m_idx in range(0, m_size, BLOCK_SIZE_M):
                    m_block_size = tl.minimum(BLOCK_SIZE_M, m_size - tile_m_idx)

                    if m_block_size > 0:
                        # Global offset for this chunk
                        m_global_offset = m_start + tile_m_idx
                        m_offsets = m_global_offset + block_range_m

                        if PERMUTE_X or PERMUTE_Y:
                            # These will be used for loading and storing in permuted order
                            gather_offsets = (
                                tile_m_idx + block_range_m
                            )  # NOTE: tile_m_idx is already strided by BLOCK_SIZE_M

                            indices_to_gather = m_start + tl.max_contiguous(
                                tl.multiple_of(gather_offsets % m_size, BLOCK_SIZE_M),
                                BLOCK_SIZE_M,
                            )
                            # indices_to_gather = m_start + gather_offsets
                            expert_token_idx = tl.load(
                                gather_indices_ptr + indices_to_gather,
                                mask = indices_to_gather < TOTAL_TOKENS,
                            )
                            expert_token_offsets = expert_token_idx[:, None]

                            # Masks for permuted load and store
                            row_load_mask = gather_offsets < m_size

                            # We only take into account the following two cases: (PERMUTE_X and NOT PERMUTE_Y) and (NOT PERMUTE_X and PERMUTE_Y)
                            # Hence, we can make the following simplifying assumptions when loading and storing
                            # Note the different strides between the two cases: the offsets for loading and storing are flipped and the strides must also be adjusted
                            if PERMUTE_X:
                                x_row_load_idx = (
                                    (expert_token_offsets // TOPK) * K
                                )  # Permute on load from token -> expert order, divide by TOPK to index from original number of tokens
                                dY_row_load_idx = m_offsets[:, None] * N
                            else:
                                x_row_load_idx = (
                                    indices_to_gather[:, None] * K
                                )  # Load in contiguous order (no permutation on load)
                                dY_row_load_idx = expert_token_offsets * N

                        else:
                            x_row_load_idx = m_offsets[:, None] * K
                            dY_row_load_idx = m_offsets[:, None] * N
                            row_load_mask = block_range_m < m_block_size

                        mk_mask = row_load_mask[:, None] & k_mask[None, :]
                        mn_mask = row_load_mask[:, None] & n_mask[None, :]

                        if USE_TMA_LOAD_X:
                            x = x_desc.load([m_global_offset, k_offset])
                        else:
                            x = tl.load(
                                x_ptr
                                + x_row_load_idx
                                + (k_offset + block_range_k)[None, :],
                                mask = mk_mask,
                            )

                        if USE_TMA_LOAD_dY:
                            dY = dY_desc.load([m_global_offset, n_offset])
                        else:
                            dY = tl.load(
                                dY_ptr
                                + dY_row_load_idx
                                + (n_offset + block_range_n)[None, :],
                                mask = mn_mask,
                            )

                        accumulator += tl.dot(
                            dY.T.to(x.dtype),  # [BLOCK_N, BLOCK_M]
                            x,  # [BLOCK_M, BLOCK_K]
                        )

                y = accumulator.to(output_dtype)
                if USE_TMA_STORE:
                    # Need to expand dims to match [E, N, K] shape
                    y = tl.expand_dims(y, 0)
                    dW_desc.store([expert_idx, n_offset, k_offset], y)
                else:
                    tl.store(
                        dW_ptr
                        # + (n_offset + offs_n)[:, None] * K
                        + store_row_offs[:, None] * K
                        + (k_offset + block_range_k)[None, :],
                        y,
                        mask = nk_mask,
                    )