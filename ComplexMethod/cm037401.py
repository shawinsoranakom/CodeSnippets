def init_device(self):
        device = self.device_config.device
        if (
            isinstance(device, torch.device)
            and device.type == "xpu"
            and current_platform.is_xpu()
        ):
            self.device = torch.device(f"xpu:{self.local_rank}")
            torch.accelerator.set_device_index(self.device)
            current_platform.check_if_supports_dtype(self.model_config.dtype)
            torch.accelerator.empty_cache()
            self.init_gpu_memory = torch.xpu.get_device_properties(
                self.local_rank
            ).total_memory
        else:
            raise RuntimeError(f"Not support device type: {self.device_config.device}")

        ENV_CCL_ATL_TRANSPORT = os.getenv("CCL_ATL_TRANSPORT", "ofi")
        ENV_LOCAL_WORLD_SIZE = os.getenv(
            "LOCAL_WORLD_SIZE", str(self.parallel_config.world_size)
        )
        os.environ["CCL_ATL_TRANSPORT"] = ENV_CCL_ATL_TRANSPORT
        os.environ["LOCAL_WORLD_SIZE"] = ENV_LOCAL_WORLD_SIZE
        os.environ["LOCAL_RANK"] = str(self.local_rank)

        init_worker_distributed_environment(
            self.vllm_config,
            self.rank,
            self.distributed_init_method,
            self.local_rank,
            current_platform.dist_backend,
        )

        # global all_reduce needed for overall oneccl warm up
        if torch.distributed.is_xccl_available():
            torch.distributed.all_reduce(torch.zeros(1).xpu())

        # Set random seed.
        set_random_seed(self.model_config.seed)

        # Now take memory snapshot after NCCL is initialized
        gc.collect()
        torch.accelerator.empty_cache()

        # take current memory snapshot
        self.init_snapshot = init_snapshot = MemorySnapshot(device=self.device)
        self.requested_memory = request_memory(init_snapshot, self.cache_config)
        logger.debug("worker init memory snapshot: %r", self.init_snapshot)
        logger.debug(
            "worker requested memory: %sGiB", format_gib(self.requested_memory)
        )

        # Initialize workspace manager
        num_ubatches = 2 if self.vllm_config.parallel_config.enable_dbo else 1
        init_workspace_manager(self.device, num_ubatches)

        # Construct the model runner
        model_runner = XPUModelRunnerV2 if self.use_v2_model_runner else XPUModelRunner
        self.model_runner = model_runner(  # type: ignore
            self.vllm_config, self.device
        )

        if self.rank == 0:
            # If usage stat is enabled, collect relevant info.
            report_usage_stats(self.vllm_config)