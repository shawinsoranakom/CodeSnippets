def profile(self, is_start: bool = True, profile_prefix: str | None = None):
        # Check if profiling is enabled
        if self.profiler_config is None or self.profiler_config.profiler is None:
            raise RuntimeError(
                "Profiling is not enabled. Please set --profiler-config to enable "
                "profiling. Example: "
                "'--profiler-config.profiler=torch --profiler-config.torch_profiler_dir"
                "=YOUR_DIR_PATH_TO_DUMP_TRACE'"
            )

        if is_start:
            # Generate the trace name by combining prefix with comprehensive rank suffix
            from vllm.distributed.utils import get_worker_rank_suffix

            rank_suffix = get_worker_rank_suffix(global_rank=self.rank)

            # Build the full trace name
            if profile_prefix:
                trace_name = f"{profile_prefix}_{rank_suffix}"
            else:
                trace_name = rank_suffix

            # Create the profiler wrapper only on the first start call
            if self.profiler is None:
                profiler_type = self.profiler_config.profiler
                if profiler_type == "torch":
                    self.profiler = TorchProfilerWrapper(
                        self.profiler_config,
                        worker_name=trace_name,
                        local_rank=self.local_rank,
                        activities=["CPU", "CUDA"],
                    )
                    logger.debug(
                        "Starting torch profiler with trace name: %s", trace_name
                    )
                elif profiler_type == "cuda":
                    self.profiler = CudaProfilerWrapper(self.profiler_config)
                    logger.debug("Starting CUDA profiler")
                else:
                    # Config validation should prevent this code being reached
                    raise ValueError(
                        f"Invalid profiler value of {self.profiler_config.profiler}"
                    )

            # If profiler already initialized, restart profiling but keep
            # the original trace name from the first initialization.
            self.profiler.start()
        else:
            if self.profiler is None:
                logger.warning("Profiler was not started, nothing to stop.")
                return
            self.profiler.stop()