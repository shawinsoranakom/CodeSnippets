def profile_cudagraph_memory(self) -> int:
        with set_current_vllm_config(self.vllm_config):
            self._init_minimal_kv_cache_for_profiling()

        saved_num_cudagraph_captured = compilation_counter.num_cudagraph_captured

        capture_descs = self.cudagraph_dispatcher.get_capture_descs()

        total_graphs = sum(len(descs) for _, descs in capture_descs)
        if total_graphs == 0:
            logger.debug("No CUDA graphs will be captured, skipping profiling")
            self._cleanup_profiling_kv_cache()
            return 0

        logger.info(
            "Profiling CUDA graph memory: %s",
            ", ".join(
                f"{mode.name}={len(descs)} (largest={descs[0].num_tokens})"
                for mode, descs in capture_descs
                if descs
            ),
        )

        # Use a temporary pool for profiling to avoid fragmentation in the main pool.
        profiling_pool = current_platform.graph_pool_handle()
        original_pools: dict[int, Any] = {}
        for instance in list(CUDAGraphWrapper._all_instances):
            original_pools[id(instance)] = instance.graph_pool
            instance.graph_pool = profiling_pool

        set_cudagraph_capturing_enabled(True)
        with self._freeze_gc(), graph_capture(device=self.device):
            shared_memory_estimate = {}
            per_graph_estimate = {}
            torch.accelerator.synchronize()
            torch.accelerator.empty_cache()

            for mode, descs in capture_descs:
                profile_descs = descs[:2]
                mem_samples: list[int] = []

                for i, desc in enumerate(profile_descs):
                    mem_before = torch.cuda.mem_get_info()[0]
                    self._warmup_and_capture(
                        desc,
                        cudagraph_runtime_mode=mode,
                        profile_seq_lens=(
                            min(
                                self.max_model_len,
                                self.max_num_tokens // desc.num_tokens,
                            )
                            if mode == CUDAGraphMode.FULL and i == 0
                            else None
                        ),
                    )
                    torch.accelerator.synchronize()
                    free_after = torch.cuda.mem_get_info()[0]
                    mem_samples.append(mem_before - free_after)

                first_capture = mem_samples[0]
                # Use at least 1 MiB per graph for driver overhead
                per_graph = max(mem_samples[1] if len(mem_samples) > 1 else 0, 1 << 20)

                shared_memory_estimate[mode] = first_capture
                per_graph_estimate[mode] = per_graph * (len(descs) - 1)

                logger.debug(
                    "Estimated %s CUDA graph memory: "
                    "%.2f MiB first-capture + (%d-1) × %.2f MiB per-graph",
                    mode.name,
                    first_capture / (1 << 20),
                    len(descs),
                    per_graph / (1 << 20),
                )

        set_cudagraph_capturing_enabled(False)
        CUDAGraphWrapper.clear_all_graphs()
        for instance in list(CUDAGraphWrapper._all_instances):
            if id(instance) in original_pools:
                instance.graph_pool = original_pools[id(instance)]
        for key_set in self.cudagraph_dispatcher.cudagraph_keys.values():
            key_set.clear()
        self.cudagraph_dispatcher.keys_initialized = False
        self.maybe_remove_all_loras(self.lora_config)
        self._cleanup_profiling_kv_cache()
        compilation_counter.num_cudagraph_captured = saved_num_cudagraph_captured

        # FULL and PIECEWISE graphs share the global pool at runtime and are
        # never replayed concurrently, so the pool overlays their memory.
        # Take the max to avoid double-counting the overlap.
        total_estimate = max(shared_memory_estimate.values()) + sum(
            per_graph_estimate.values()
        )
        logger.info(
            "Estimated CUDA graph memory: %.2f GiB total",
            total_estimate / (1 << 30),
        )

        return int(total_estimate)