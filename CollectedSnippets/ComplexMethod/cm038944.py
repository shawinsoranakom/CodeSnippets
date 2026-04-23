def prune_rocm_configs(M, N, K, configs, is_fp16=True):
    pruned_configs = []
    elemBytes_a = 2 if is_fp16 else 1
    elemBytes_b = 2 if is_fp16 else 1

    mfma = 16 if M < 32 or N < 32 else 32

    # TODO (zhanglx): figure out the boundary between large and small gemms
    large_gemm = False
    if M >= 2048 and N >= 2048:
        large_gemm = True

    for config in configs:
        BLOCK_SIZE_M = config.get("BLOCK_SIZE_M")
        BLOCK_SIZE_N = config.get("BLOCK_SIZE_N")
        BLOCK_SIZE_K = config.get("BLOCK_SIZE_K")
        num_warps = config.get("num_warps")

        if is_fp16:
            matrix_instr_nonkdim = config.get("matrix_instr_nonkdim")
            if matrix_instr_nonkdim > mfma:
                continue
        if mfma == 4 and BLOCK_SIZE_K < 64:
            continue
        # some layouts could not work properly in case
        # number elements per thread is less 1
        if BLOCK_SIZE_M * BLOCK_SIZE_N < 64:
            continue
        SPLIT_K = config.get("SPLIT_K", 1)
        GROUP_M = config.get("GROUP_SIZE_M")
        if is_fp16:
            if (
                matrix_instr_nonkdim > BLOCK_SIZE_M
                or matrix_instr_nonkdim > BLOCK_SIZE_N
            ):
                continue
            if matrix_instr_nonkdim >= M and matrix_instr_nonkdim != BLOCK_SIZE_M:
                continue
            if matrix_instr_nonkdim >= N and matrix_instr_nonkdim != BLOCK_SIZE_N:
                continue
        # Skip BLOCK_SIZE that is too large compare to M/N
        # unless BLOCK_SIZE is already small enough
        if M * 2 < BLOCK_SIZE_M and BLOCK_SIZE_M != 16:
            continue
        if N * 2 < BLOCK_SIZE_N and BLOCK_SIZE_N != 16:
            continue
        # skip large split_k when not necessary
        if SPLIT_K != 1 and not need_split_k(M, N, K):
            continue
        # skip split_k that leads to EVEN_K = false
        leap = SPLIT_K * BLOCK_SIZE_K
        modv = K % leap
        if modv != 0:
            continue
        # skip large GROUP_M
        if GROUP_M * BLOCK_SIZE_M > M and GROUP_M != 1:
            continue
        # out of shared memory resource
        # TODO (zhanglx): This does not consider the LDS usage in the epilogue
        LDS = (
            BLOCK_SIZE_K * BLOCK_SIZE_M * elemBytes_a
            + BLOCK_SIZE_K * BLOCK_SIZE_N * elemBytes_b
        )
        if LDS > 65536:
            continue
        # Skip small block sizes and num_warps for large gemm
        # For fp16 and f8, we want to only use BLOCK_SIZE >= 64
        if large_gemm:
            if BLOCK_SIZE_M < 64 or BLOCK_SIZE_N < 64:
                continue
            if BLOCK_SIZE_K < 64:
                continue
            if num_warps < 4:
                continue

        pruned_configs.append(config)

    return pruned_configs