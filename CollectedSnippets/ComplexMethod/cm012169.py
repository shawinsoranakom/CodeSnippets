def _align_compute_nodes_runtime_estimations_across_all_distributed_ranks(
        self,
    ) -> None:
        """Align runtime estimations across ranks (compute + collectives)."""
        log.info(
            "Overlap scheduling: Aligning runtime estimations across all distributed ranks"
        )

        # Benchmark compute nodes
        runtime_estimations_keys: list[str | None] = []
        runtime_estimations: list[float] = []
        compute_key_count = 0

        # Also collect analytical estimations for logging
        runtime_estimations_analytical: list[float] = []

        for n in self.compute_nodes:
            # Compute analytical estimation using roofline model
            val_analytical = estimate_roofline_runtime_ms(n)
            runtime_estimations_analytical.append(val_analytical)

            if self.compute_estimator == "benchmark":
                val, key = benchmark_node_with_cache_key(
                    n, self.custom_runtime_estimation
                )
            else:
                # Use analytical estimation
                val, key = val_analytical, None

            runtime_estimations.append(val)
            runtime_estimations_keys.append(key)
            compute_key_count += 1

        # Log compute estimations
        from torch._inductor.fx_passes.node_runtime_estimation import (
            _log_compute_estimations,
        )

        _log_compute_estimations(
            self.compute_nodes,
            runtime_estimations,
            runtime_estimations_analytical,
        )

        # Benchmark collectives if enabled (only CUDA events - others are deterministic)
        # Skip if custom estimation is provided for collectives
        collective_nodes: list[fx.Node] = []
        benchmarked_collective_nodes: list[
            fx.Node
        ] = []  # Track which were actually benchmarked
        if self.collective_estimator == "benchmark":
            from torch._inductor.fx_passes.node_runtime_estimation import (
                benchmark_collective_with_cuda_events,
            )

            collective_nodes = [
                info.start_node for info in self.collective_info.values()
            ]

            # Benchmark CUDA events (non-deterministic, needs alignment)
            # Skip collectives with custom estimation
            for n in collective_nodes:
                if (
                    get_custom_estimation(n, self.custom_runtime_estimation, None)
                    is not None
                ):
                    continue

                # Benchmark actual size
                cuda_val, cuda_key = benchmark_collective_with_cuda_events(n, nruns=5)
                if cuda_val is not None:
                    runtime_estimations.append(cuda_val)
                    runtime_estimations_keys.append(cuda_key)
                    benchmarked_collective_nodes.append(n)

        # When both estimators are analytical, estimates are deterministic across ranks
        # (same shapes = same estimates), so skip the all_gather to avoid sync.
        import torch.distributed as dist

        world_size = dist.get_world_size()

        if (
            self.compute_estimator == "analytical"
            and self.collective_estimator == "analytical"
        ):
            median_runtime_estimations = runtime_estimations
        else:
            # Single all_gather and compute medians
            from torch._subclasses.fake_tensor import unset_fake_temporarily
            from torch.distributed.distributed_c10d import _get_default_group

            pg = _get_default_group()
            with unset_fake_temporarily():
                gathered_runtime_estimations: list[list[float]] = [
                    [] for _ in range(world_size)
                ]
                dist.all_gather_object(
                    gathered_runtime_estimations, runtime_estimations, pg
                )
                median_runtime_estimations = torch.median(
                    torch.tensor(gathered_runtime_estimations), dim=0
                ).values.tolist()

        # Cache medians
        collective_keys = []
        collective_medians = []
        for idx, (key, median_runtime_estimation) in enumerate(
            zip(runtime_estimations_keys, median_runtime_estimations)
        ):
            if key is None:
                continue
            if idx < compute_key_count:
                # Compute node
                self.node_estimations[self.compute_nodes[idx]] = (
                    median_runtime_estimation
                )
                set_cached_node_time(key, median_runtime_estimation)
            else:
                # Collective CUDA event benchmark
                from torch._inductor.fx_passes.node_runtime_estimation import (
                    set_cached_runtime,
                )

                set_cached_runtime(key, median_runtime_estimation)

                # Update CollectiveInfo with aligned benchmark
                coll_idx = idx - compute_key_count
                coll_node = benchmarked_collective_nodes[coll_idx]
                info = self.collective_info[coll_node]
                info.estimated_time_ms = median_runtime_estimation
                info.exposed_time_ms = median_runtime_estimation
                self.node_estimations[coll_node] = median_runtime_estimation

                collective_keys.append(key)
                collective_medians.append(median_runtime_estimation)

        # Log benchmarks with analytical comparisons
        if collective_keys:
            from torch._inductor.fx_passes.node_runtime_estimation import (
                _log_collective_benchmarks,
            )

            _log_collective_benchmarks(
                benchmarked_collective_nodes,
                collective_keys,
                collective_medians,
                world_size,
                "fx_collectives_node_runtime_estimation",
            )
        else:
            # No benchmarking - log analytical estimations for all collectives
            from torch._inductor.fx_passes.node_runtime_estimation import (
                _log_collective_benchmarks,
            )

            all_collective_nodes = [
                info.start_node for info in self.collective_info.values()
            ]
            if all_collective_nodes:
                _log_collective_benchmarks(
                    all_collective_nodes,
                    artifact_name="fx_collectives_analytical_estimation",
                )

        log.info("Overlap scheduling: Runtime estimations aligned")