def _get_heuristic_configs(
        self,
        m: int,
        n: int,
        k: int,
        dtype_a: torch.dtype,
        layout_a: str,
        layout_b: str,
        count: int,
        valid_configs: OrderedSet[ConfigKey],
        accumulator_type: torch.dtype = torch.float32,
        batch_size: int = 1,
        dtype_b: torch.dtype | None = None,
        out_dtype: torch.dtype | None = None,
    ) -> list[HeuristicConfig]:
        """
        Get kernel configurations recommended by nvMatmulHeuristics.

        Uses validity callback to filter to cutlass_api-compatible configs.
        """
        import nvMatmulHeuristics

        dtype_to_cublas = {
            torch.float64: "D",
            torch.float32: "S",
            torch.float16: "H",
            torch.bfloat16: "T",
            torch.float8_e4m3fn: "Q",
            torch.float8_e5m2: "R",
            torch.float4_e2m1fn_x2: "F4",
        }
        a_char = dtype_to_cublas.get(dtype_a, "H")
        b_char = dtype_to_cublas.get(dtype_b or dtype_a, a_char)
        out_char = dtype_to_cublas.get(out_dtype or dtype_a, a_char)
        acc_char = dtype_to_cublas.get(accumulator_type, "S")

        # nvMatmulHeuristics precision string formats:
        # - 3-letter {A}{B}{out}: used for standard GEMM and multi-char tokens (F4, BF)
        # - 5-letter {A}{B}{C}{compute}{D}: used for single-char FP8 types (Q, R, O)
        has_multichar = any(len(c) > 1 for c in (a_char, b_char, out_char))
        if has_multichar:
            precision = f"{a_char}{b_char}{out_char}"
        elif a_char != b_char or a_char in ("Q", "R", "O"):
            precision = f"{a_char}{b_char}{out_char}{acc_char}{out_char}"
        else:
            precision = f"{a_char}{acc_char}{out_char}"

        # NvMatmulHeuristicsInterfaceEx configuration:
        # - backend=CUTLASS3: Use CUTLASS 3.x kernel database for Hopper+ GPUs
        #   TODO(nikhilap): Update when nvMatmulHeuristics supports CUTLASS 4
        # - flags=PERF_MODEL_BASED_AUTO_TUNING: Rank kernels using analytical
        #   performance model (faster than empirical profiling)
        # - load_discovery_implicitly=True: Auto-load kernel discovery sets on demand
        lh = nvMatmulHeuristics.NvMatmulHeuristicsInterfaceEx(
            backend=nvMatmulHeuristics.NvMatmulHeuristicsTarget.CUTLASS3,
            flags=nvMatmulHeuristics.NvMatmulHeuristicsFlags.PERF_MODEL_BASED_AUTO_TUNING,
            load_discovery_implicitly=True,
        )

        backend = lh.createBackend(nvMatmulHeuristics.NvMatmulHeuristicsTarget.CUTLASS3)

        validity_callback = self._make_validity_callback(valid_configs)
        lh.setBackendCallbackProperty(
            backend,
            nvMatmulHeuristics.NvMatmulHeuristicsBackendPropertyCallbackKind.KERNEL_ADDITIONAL_VALIDITY_CHECK,
            validity_callback,
        )

        layout = self._get_layout_enum(layout_a, layout_b)

        lh.loadInternalDiscoverySet(layout, precision=precision)

        problem = lh.makeNvMatmulHeuristicsProblem(
            m, n, k, layout, batch_size=batch_size
        )
        raw_configs = lh.getEx(problem, count, backend, precision=precision)
        lh.destroyBackend(backend)

        if not raw_configs:
            autotuning_log.debug(
                "nvMatmulHeuristics returned 0 configs for M=%d, N=%d, K=%d, "
                "dtype=%s, layout=(%s, %s), precision=%s",
                m,
                n,
                k,
                dtype_a,
                layout_a,
                layout_b,
                precision,
            )
            return []

        configs = []
        for cfg in raw_configs:
            kernel = cfg["kernel"]
            configs.append(
                HeuristicConfig(
                    tile_m=kernel.cta_tile_m,
                    tile_n=kernel.cta_tile_n,
                    tile_k=kernel.cta_tile_k,
                    cluster_m=kernel.cluster_m,
                    cluster_n=kernel.cluster_n,
                    stages=kernel.stages,
                    split_k=kernel.split_k,
                    warp_tile_m=kernel.warp_tile_m,
                    warp_tile_n=kernel.warp_tile_n,
                    warp_tile_k=kernel.warp_tile_k,
                    estimated_runtime=cfg["runtime"],
                )
            )

        autotuning_log.info(
            "nvMatmulHeuristics for M=%d, N=%d, K=%d, dtype=%s, layout=(%s, %s), "
            "precision=%s: %d configs returned",
            m,
            n,
            k,
            dtype_a,
            layout_a,
            layout_b,
            precision,
            len(configs),
        )
        for i, cfg in enumerate(configs):
            runtime_us = cfg.estimated_runtime * 1e6
            autotuning_log.info(
                "  Config %d: tile=(%d, %d, %d), cluster=(%d, %d), "
                "stages=%d, split_k=%d, warp_tile=(%d, %d, %d), "
                "estimated_runtime=%.2f us",
                i,
                cfg.tile_m,
                cfg.tile_n,
                cfg.tile_k,
                cfg.cluster_m,
                cfg.cluster_n,
                cfg.stages,
                cfg.split_k,
                cfg.warp_tile_m,
                cfg.warp_tile_n,
                cfg.warp_tile_k,
                runtime_us,
            )

        return configs