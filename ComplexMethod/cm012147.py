def filter_kernels(
        self,
        kernels: list,
        inputs: MMKernelInputs,
        count: int,
        accumulator_type: torch.dtype = torch.float32,
    ) -> list:
        """
        Filter and rank kernels using nvMatmulHeuristics.

        Matches on (tile_m, tile_n, tile_k, cluster_m, cluster_n).
        Returns kernels sorted by estimated runtime.

        If nvMatmulHeuristics is not installed or max_autotune is disabled,
        returns the first `count` kernels without heuristic ranking.

        Args:
            kernels: List of cutlass_api.Kernel objects
            inputs: MMKernelInputs with matrix shapes, dtypes, and strides
            count: Maximum number of kernels to return
            accumulator_type: Accumulator dtype

        Returns:
            Filtered list of kernels, sorted by estimated performance
        """
        if not self.should_run(inputs):
            return kernels[:count]

        m, n, k = inputs.mnk_hinted()
        batch_size = inputs.batch_hinted()
        dtype_a = inputs.dtype(inputs._mat1_idx)
        dtype_b = inputs.dtype(inputs._mat2_idx)
        out_dtype = inputs.out_dtype()
        strides = inputs.strides_hinted()
        layout_a = "row" if strides[inputs._mat1_idx][-1] == 1 else "col"
        layout_b = "row" if strides[inputs._mat2_idx][-1] == 1 else "col"

        config_to_kernels = self._extract_config_to_kernels(kernels)

        if not config_to_kernels:
            log.debug("Could not extract kernel configs, using first %d kernels", count)
            return kernels[:count]

        heuristic_configs = self._get_heuristic_configs(
            m,
            n,
            k,
            dtype_a,
            layout_a,
            layout_b,
            count,
            OrderedSet(config_to_kernels.keys()),
            accumulator_type,
            batch_size,
            dtype_b=dtype_b,
            out_dtype=out_dtype,
        )

        if not heuristic_configs:
            log.debug("No heuristic configs found, using first %d kernels", count)
            return kernels[:count]

        # Match kernels to heuristic configs
        matched: list[tuple] = []
        for cfg in heuristic_configs:
            key = _make_config_key_from_heuristic(cfg)
            kernels_for_key = config_to_kernels.get(key)
            if not kernels_for_key:
                continue
            for kernel in kernels_for_key:
                matched.append((kernel, cfg.estimated_runtime))

        if not matched:
            log.debug(
                "No kernels matched heuristic configs, using first %d kernels", count
            )
            return kernels[:count]

        matched.sort(key=lambda x: x[1])
        selected = matched[:count]
        result = [k for k, _ in selected]

        log.debug(
            "Heuristic filtered to %d kernels from %d total", len(result), len(kernels)
        )

        autotuning_log.info(
            "nvMatmulHeuristics kernel filtering: %d heuristic configs matched %d "
            "of %d available kernels, returning top %d",
            len(heuristic_configs),
            len(matched),
            len(kernels),
            len(result),
        )
        for i, (kernel, runtime) in enumerate(selected):
            design = kernel.metadata.design
            autotuning_log.info(
                "  Selected kernel %d: tile=(%d, %d, %d), cluster=(%d, %d), "
                "estimated_runtime=%.2f us",
                i,
                design.tile_shape[0],
                design.tile_shape[1],
                design.tile_shape[2],
                design.cluster_shape[0],
                design.cluster_shape[1],
                runtime * 1e6,
            )

        return result