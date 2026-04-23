def determine_available_memory(self) -> int:
        """Profiles the peak memory usage of the model to determine how much
        memory can be used for KV cache without OOMs.

        The engine will first conduct a profiling of the existing memory usage.
        Then, it calculates the free memory that can be used for KV cache in
        bytes.

        Tip:
            You may limit the usage of GPU memory
            by adjusting the `gpu_memory_utilization` parameter.
        """
        if kv_cache_memory_bytes := self.cache_config.kv_cache_memory_bytes:
            # still need a profile run which compiles the model for
            # max_num_batched_tokens
            self.model_runner.profile_run()

            msg = (
                f"Initial free memory {format_gib(self.init_snapshot.free_memory)} "
                f"GiB, reserved {format_gib(kv_cache_memory_bytes)} GiB memory for "
                "KV Cache as specified by kv_cache_memory_bytes config and "
                "skipped memory profiling. This does not respect the "
                "gpu_memory_utilization config. Only use kv_cache_memory_bytes "
                "config when you want manual control of KV cache memory "
                "size. If OOM'ed, check the difference of initial free "
                "memory between the current run and the previous run "
                "where kv_cache_memory_bytes is suggested and update it "
                "correspondingly."
            )
            logger.info(msg)
            return kv_cache_memory_bytes

        # Execute a forward pass with dummy inputs to profile the memory usage
        # of the model.
        with memory_profiling(
            self.init_snapshot,
            weights_memory=int(self.model_runner.model_memory_usage),
        ) as profile_result:
            self.model_runner.profile_run()

            profile_torch_peak = torch.accelerator.memory_stats(self.device).get(
                "allocated_bytes.all.peak", 0
            )

            # Profile CUDA graph memory if graphs will be captured.
            # Skip on ROCm/HIP/XPU as graph pool handles and mem_get_info behave
            # differently and can produce incorrect/negative estimates.
            cudagraph_memory_estimate = 0
            if (
                not current_platform.is_rocm()
                and self.vllm_config.compilation_config.cudagraph_mode
                != CUDAGraphMode.NONE
            ):
                cudagraph_memory_estimate = self.model_runner.profile_cudagraph_memory()

        # Use the pre-cudagraph torch peak to avoid double-counting.
        profile_result.torch_peak_increase = (
            profile_torch_peak - profile_result.before_profile.torch_peak
        )
        profile_result.non_kv_cache_memory = (
            profile_result.non_torch_increase
            + profile_result.torch_peak_increase
            + profile_result.weights_memory
        )

        # On ROCm, cudagraph_memory_estimate is always 0 so this is a no-op.
        # On CUDA, respect the opt-in flag as originally designed.
        cudagraph_memory_estimate_applied = (
            cudagraph_memory_estimate
            if envs.VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS
            else 0
        )

        self.non_torch_memory = profile_result.non_torch_increase
        self.peak_activation_memory = profile_result.torch_peak_increase
        self.cudagraph_memory_estimate = cudagraph_memory_estimate

        free_gpu_memory = profile_result.after_profile.free_memory
        # NOTE(woosuk): Here we assume that the other processes using the same
        # GPU did not change their memory usage during the profiling.
        assert self.init_snapshot.free_memory >= free_gpu_memory, (
            "Error in memory profiling. "
            f"Initial free memory {format_gib(self.init_snapshot.free_memory)} GiB, "
            f"current free memory {format_gib(free_gpu_memory)} GiB. "
            "This happens when other processes sharing the same container "
            "release GPU memory while vLLM is profiling during initialization. "
            "To fix this, ensure consistent GPU memory allocation or "
            "isolate vLLM in its own container."
        )
        self.available_kv_cache_memory_bytes = (
            self.requested_memory
            - profile_result.non_kv_cache_memory
            - cudagraph_memory_estimate_applied
        )

        unrequested_memory = self.init_snapshot.free_memory - self.requested_memory
        logger.debug(
            "Initial free memory: %s GiB; Requested memory: %f (util), %s GiB",
            format_gib(self.init_snapshot.free_memory),
            self.cache_config.gpu_memory_utilization,
            format_gib(self.requested_memory),
        )
        logger.debug(
            "Free memory after profiling: %s GiB (total), %s GiB (within requested)",
            format_gib(free_gpu_memory),
            format_gib(free_gpu_memory - unrequested_memory),
        )
        logger.debug(profile_result)
        logger.info_once(
            "Available KV cache memory: %s GiB",
            format_gib(self.available_kv_cache_memory_bytes),
        )

        if cudagraph_memory_estimate > 0:
            total_mem = self.init_snapshot.total_memory
            current_util = self.cache_config.gpu_memory_utilization
            cg_util_delta = cudagraph_memory_estimate / total_mem
            if envs.VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS:
                equiv_util = round(current_util - cg_util_delta, 4)
                suggested_util = min(
                    round(current_util + cg_util_delta, 4),
                    1.0,
                )
                logger.info(
                    "CUDA graph memory profiling is enabled (default since "
                    "v0.21.0). The current --gpu-memory-utilization=%.4f is "
                    "equivalent to --gpu-memory-utilization=%.4f without "
                    "CUDA graph memory profiling. To maintain the same "
                    "effective KV cache size as before, increase "
                    "--gpu-memory-utilization to %.4f. To disable, set "
                    "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0.",
                    current_util,
                    equiv_util,
                    suggested_util,
                )
            else:
                suggested_util = min(
                    round(current_util + cg_util_delta, 4),
                    1.0,
                )
                logger.warning(
                    "CUDA graph memory profiling is disabled "
                    "(VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0). "
                    "Without it, CUDA graph memory is not accounted for "
                    "during KV cache allocation, which may require lowering "
                    "--gpu-memory-utilization to avoid OOM. Consider "
                    "re-enabling it (the default as of v0.21.0) and increasing "
                    "--gpu-memory-utilization from %.4f to %.4f.",
                    current_util,
                    suggested_util,
                )

        return int(self.available_kv_cache_memory_bytes)