def get_all(cls) -> list["BwdKernel"]:
        kernels: list[BwdKernel] = []
        for aligned, dtype, (sm, sm_max), apply_dropout, max_k in itertools.product(
            [True, False],
            DTYPES.keys(),
            SM_RANGES,
            [True, False],
            [32, 64, 128, 2**16],
        ):
            if dtype == "bf16" and sm < 80:
                continue
            if not aligned and sm >= 80:
                continue
            is_half = dtype in ["bf16", "f16"]

            bi_values = [64]
            # Some architectures have more shmem and can use 128
            # We still need fallback to 64 for GPUs with less shmem
            # (Sm75, Sm86 ...)
            if sm >= 80 or (sm >= 70 and is_half):
                if max_k > 64:
                    bi_values.append(128)
            for bi in bi_values:
                output_in_rf = is_half and max_k <= bi
                preload_mmas = is_half and sm >= 80 and output_in_rf
                bj = 128 if (preload_mmas and max_k > 64) else 64
                kernels.append(
                    cls(
                        aligned=aligned,
                        dtype=dtype,
                        sm_range=(sm, sm_max),
                        apply_dropout=apply_dropout,
                        preload_mmas=preload_mmas,
                        block_i=bi,
                        block_j=bj,
                        max_k=max_k,
                    )
                )
                # A few specialized kernels that are faster
                if apply_dropout or max_k > 128 or not is_half or not aligned:
                    continue
                if sm not in [70, 80]:
                    continue
                kernels.append(
                    cls(
                        aligned=aligned,
                        dtype=dtype,
                        sm_range=(sm, sm_max),
                        apply_dropout=apply_dropout,
                        preload_mmas=preload_mmas,
                        block_i=bi,
                        block_j=bj,
                        max_k=max_k,
                        keys_queries_aligned_to_blocksizes=True,
                    )
                )
        # Add some specialized kernels for stable diffusion BW (K=80)
        # This is the only kernel that can keep the outputs on RF on
        # Sm86/Sm89, so it's much faster than the 64x64 one
        sm80_range = next(sm_range for sm_range in SM_RANGES if sm_range[0] == 80)
        for dtype in ["f16", "bf16"]:
            kernels.append(
                cls(
                    aligned=True,
                    dtype=dtype,
                    sm_range=sm80_range,
                    apply_dropout=False,
                    preload_mmas=True,
                    block_i=128,
                    block_j=64,
                    max_k=96,
                    # Sm80 has a faster kernel for this case
                    dispatch_cond="cc == 86 || cc == 89",
                )
            )
        return kernels