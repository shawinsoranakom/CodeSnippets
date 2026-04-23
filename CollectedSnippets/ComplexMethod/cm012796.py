def persistent_reduction(
    size_hints,
    reduction_hint=False,
    triton_meta=None,
    filename=None,
    inductor_meta=None,
    return_configs=False,
):
    """Generate persistent reductions + mix-order if available"""
    inductor_meta = {} if inductor_meta is None else inductor_meta
    inductor_meta["reduction_hint"] = reduction_hint
    if inductor_meta.get("no_x_dim"):
        size_hints["x"] = 1

    configs = _handle_combo_kernel_per_subkernel_blocks(
        size_hints,
        inductor_meta,
        triton_meta,
        filename=filename,
        reduction_hint=reduction_hint,
    )
    if configs is not None:
        return cached_autotune(
            None,
            configs,
            triton_meta=triton_meta,
            inductor_meta=inductor_meta,
            heuristic_type=HeuristicType.PERSISTENT_REDUCTION,
            filename=filename,
        )

    configs = _persistent_reduction_configs(
        size_hints, reduction_hint, inductor_meta, triton_meta
    )

    # This key is not added to the inductor meta as its clear from the heuristic
    # choice that it is persistent. Add it and remove it below so that persistent
    # configs can be filtered appropriately by _maybe_filter_configs_for_tma_restrictions
    persistent_reduction_key = "persistent_reduction"
    inductor_meta[persistent_reduction_key] = True
    configs = _maybe_filter_configs_for_tma_restrictions(inductor_meta, configs)
    inductor_meta.pop(persistent_reduction_key)

    max_autotune_enabled = inductor_meta.get("max_autotune") or inductor_meta.get(
        "max_autotune_pointwise"
    )

    if inductor_meta.get("RSPLIT_SIZE"):
        new_configs = []
        rsplit_size = inductor_meta.get("RSPLIT_SIZE")
        rnumel_hint = size_hints["r0_"]
        min_x_block = 1
        if rnumel_hint <= 512:
            min_x_block = 4
        # If TMA tensor descriptors are in use, Triton requires the last dimension
        # of a descriptor's block_shape to cover at least 16 bytes.
        # Codegen records such minimums in `tma_min_block_sizes`.
        # Ensuring our RSPLIT-driven XBLOCK override does not violate them.
        required_x_block = 1
        if (
            tma_min_block_sizes := inductor_meta.get("tma_min_block_sizes")
        ) is not None:
            required_x_block = max(
                required_x_block, tma_min_block_sizes.get("XBLOCK", 1)
            )
        x_block = min(max(rsplit_size // 32, min_x_block, required_x_block), 16)
        for c in configs:
            c.kwargs["RSPLIT_SIZE"] = rsplit_size
            # small XBLOCK to use less registers/smem
            c.kwargs["XBLOCK"] = x_block

            num_iters = rsplit_size // x_block

            # With large rnumel, we have higher chance of out-of-shared memory
            # To avoid adding too much autotuning overhead, we just constrain NUM_STAGES
            # if rnumel is large
            if inductor_meta.get("mix_order_reduction_allow_multi_stages", True):
                MAX_NUM_STAGES = 2 if rnumel_hint > 8192 else 3
            else:
                MAX_NUM_STAGES = 1
            c.kwargs["NUM_STAGES"] = min(max(num_iters // 4, 1), MAX_NUM_STAGES)

            if rnumel_hint <= 1024:
                c.num_warps //= 2
                c.num_warps = max(c.num_warps, 1)
                new_configs.append(c)

                if max_autotune_enabled:
                    # less warps so potentially each sm can run more thread blocks
                    # Inside each thread block, we handle the split sequentially,
                    # more thread blocks is beneficial here.
                    newc = copy.deepcopy(c)
                    newc.num_warps = 2
                    new_configs.append(newc)
            else:
                # more warps for larger rows
                new_configs.append(c)

                max_warps_limit = 16 if torch.version.hip else 32
                if max_autotune_enabled and c.num_warps < max_warps_limit:
                    newc = copy.deepcopy(c)
                    newc.num_warps *= 2
                    new_configs.append(newc)
        configs = unique_configs(new_configs)

    configs = filter_reduction_configs_for_determinism(inductor_meta, configs)

    if return_configs:
        return configs

    return cached_autotune(
        size_hints,
        configs,
        triton_meta=triton_meta,
        inductor_meta=inductor_meta,
        filename=filename,
        heuristic_type=HeuristicType.PERSISTENT_REDUCTION,
    )