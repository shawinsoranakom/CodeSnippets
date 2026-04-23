def _reduction_configs(
    *,
    size_hints: dict[str, int],
    inductor_meta: dict[str, Any],
    triton_meta: dict[str, Any],
    num_dynamic=0,
) -> list[Config]:
    reduction_hint = inductor_meta.get("reduction_hint")

    # Convert reductions to 1D, to simplify heuristics.
    rnumel = get_total_reduction_numel(size_hints)

    # Is max autotune enabled
    max_autotune_enabled = inductor_meta.get("max_autotune") or inductor_meta.get(
        "max_autotune_pointwise"
    )

    register_intensive = False
    loads_and_red = inductor_meta.get("num_load", 0) + inductor_meta.get(
        "num_reduction", 0
    )

    device_major = triton_meta["device"].major
    # Prefer smaller MAX_R0_BLOCK for Blackwell
    MAX_R0_BLOCK = 1024 if device_major is not None and device_major >= 10 else 2048
    if size_hints["x"] >= 1024 and loads_and_red >= 10:
        # A heuristics to reduce R0_BLOCK if a kernel potentially need many registers.
        # Consider load and reduction since load need move data into registers and
        # reduction needs an accumulator.
        #
        # The magic numbers are a bit arbitrary.
        #
        # We cannot rely on dynamically scaling down R0_BLOCK later, since sometimes
        # triton makes it to use less registers with worse perf. Check:
        # https://github.com/pytorch/pytorch/issues/126463
        #
        # The heuristic is a very simple one since registers can be reused. But
        # hopefully it can be a good enough indicator.
        MAX_R0_BLOCK = 1024
        register_intensive = True

    if triton_meta.get("native_matmul"):
        if len(size_hints) == 3:
            return [
                make_matmul_triton_config(sizes, num_warps, num_stages)
                for sizes, num_warps, num_stages in triton_native_mm_configs
            ]
        elif len(size_hints) == 4:
            return [
                make_matmul_triton_config(sizes, num_warps, num_stages)
                for sizes, num_warps, num_stages in triton_native_bmm_configs
            ]
        else:
            raise NotImplementedError("native matmul only supports mm/bmm pattern")

    def make_config(
        x,
        r,
        num_warps=None,
        num_stages=1,
        register_intensive=False,
        dynamic_scale_rblock=True,
        waves_per_eu=None,
    ):
        # For 3D case with tiling scores, create an adapted version
        if "y" in size_hints:
            tiling_scores = _get_tiling_scores(inductor_meta, size_hints)
            return adapt_config_for_tiling(
                size_hints,
                tiling_scores,
                x,
                r,
                num_warps=num_warps,
                num_stages=num_stages,
                register_intensive=register_intensive,
                waves_per_eu=waves_per_eu,
            )
        else:
            # For other cases, use the original function
            return triton_config_reduction(
                size_hints,
                x,
                r,
                num_warps=num_warps,
                num_stages=num_stages,
                register_intensive=register_intensive,
                waves_per_eu=waves_per_eu,
                dynamic_scale_rblock=dynamic_scale_rblock,
                reduction_hint=reduction_hint,
            )

    def outer_config_opt():
        # Default to 64 for vectorized loads
        max_x_block, x_block = 256, 64
        load_factor = inductor_meta.get("num_load", 0)
        x = size_hints["x"]
        num_warps = None

        # Try to use all SMs with small x
        if x <= 1024:
            x_block = max(min(x // 128, 8), 2)
            outer_r_block = min(rnumel, 64)
        # Lower bound x = 1024, 1024 // 16 = 128 around # of SMs
        elif x // 4096 <= 8:
            x_block = 16
            outer_r_block = 512 // x_block
        elif num_dynamic > 1:
            # Lots of compute with multiple dynamic shape per loop iteration
            # Larger RBLOCK minimizes loop iteration
            outer_r_block = max(min((rnumel // 64), 64), 8)
        elif num_dynamic == 1:
            # Dynamic shapes introduce a lot register pressure for indexing
            outer_r_block = (
                1
                if load_factor >= 3
                else min(next_power_of_2(max(rnumel, 128) // 128), 8)
            )
        else:
            x_block = max(min(max_x_block, next_power_of_2(x // 4096)), x_block)
            if load_factor < 4 or rnumel <= 128:
                outer_r_block = 512 // x_block
            else:
                # Heavier reductions contain a lot more overhead per loop iteration
                # We minimize the overhead by enlarging r block
                if rnumel >= 2048:
                    outer_r_block = 64
                else:
                    outer_r_block = 32
                x_block = min(x_block, 32)
                num_warps = 4

        # Set register intensive to true by default as we try to maximize tiles with heuristic
        return make_config(
            x_block,
            outer_r_block,
            num_warps=num_warps,
            register_intensive=register_intensive,
        )

    contiguous_config = make_config(
        2 if rnumel <= 2048 else 1,  # 1024 or less is persistent
        min(rnumel, MAX_R0_BLOCK),
        register_intensive=register_intensive,
    )
    tiny_config = make_config(
        2 * (256 // rnumel) if rnumel <= 256 else 1,
        min(rnumel, MAX_R0_BLOCK),
        register_intensive=register_intensive,
    )

    outer_config = make_config(64, 8, register_intensive=register_intensive)
    # TODO (paulzhan): Test heuristic on AMD and internal testing
    # for correctness
    if not torch.version.hip:
        outer_config = outer_config_opt()

    configs = []

    if inductor_meta.get("add_persistent_rblock") and loads_and_red <= 8:
        xnumel = max(4096 // rnumel, 1)
        c = make_config(
            xnumel,
            min(rnumel, 32768),
            register_intensive=register_intensive,
            dynamic_scale_rblock=False,
        )
        configs.append(c)

    result_configs = []

    # For 3d tiling, default to more autotuning initially
    if "y" in size_hints:
        pass
    elif max_autotune_enabled:
        pass  # skip all these cases
    elif reduction_hint == ReductionHint.INNER:
        return configs + [contiguous_config]
    elif reduction_hint == ReductionHint.OUTER:
        return configs + [outer_config]
    elif reduction_hint == ReductionHint.OUTER_TINY:
        return configs + [tiny_config]

    # We continue here under the following conditions:
    # - max_autotune_enabled is True
    # - max_autotune_enabled is False and reduction_hint is NOT one of the above cases
    result_configs = configs + [
        contiguous_config,
        outer_config,
        tiny_config,
        make_config(64, 64),
        make_config(8, 512),
        # halve the XBLOCK/Rn_BLOCK compared to outer_config
        # TODO: this may only be beneficial when each iteration of the reduction
        # is quite heavy. E.g. https://gist.github.com/shunting314/189a8ef69f90db9d614a823385147a72
        make_config(64, 4, num_warps=8),
    ]

    if torch.version.hip:
        hip_configs = [
            make_config(1024, 8, num_warps=4, num_stages=1, waves_per_eu=2),
            make_config(512, 8, num_warps=4, num_stages=1, waves_per_eu=1),
        ]
        result_configs.extend(hip_configs)

        # Filter ALL configs (not just HIP-specific ones) when a combo kernel
        # has a persistent sub-kernel with a large hardcoded R0_BLOCK.  The
        # persistent tile size (XBLOCK * max_persistent_rblock) causes
        # pathological ROCm compilation times (e.g. 64 * 1024 = 64K elements
        # → 60+ min triton.compile).  Use the same 4096-element threshold as
        # _persistent_reduction_configs.
        max_persistent_rblock = inductor_meta.get("max_persistent_rblock", 0)
        if max_persistent_rblock > 0:
            result_configs = [
                c
                for c in result_configs
                if c.kwargs.get("XBLOCK", 0) * max_persistent_rblock <= 4096
            ]

    return result_configs