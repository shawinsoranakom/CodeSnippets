def __init__(
        self,
        vllm_config: VllmConfig,
        role: KVConnectorRole,
        kv_cache_config: "KVCacheConfig | None" = None,
    ):
        super().__init__(vllm_config, role, kv_cache_config)

        enable_prefix_caching = vllm_config.cache_config.enable_prefix_caching
        extra_config = self._kv_transfer_config.kv_connector_extra_config or {}

        cpu_capacity_bytes = int(
            extra_config.get("cpu_bytes_to_use", DEFAULT_CPU_CAPACITY_BYTES)
        )
        # cpu_bytes_to_use is server-wide for compatibility;
        # cpu_bytes_to_use_per_rank overrides for per-rank capacity.
        world_size = vllm_config.parallel_config.world_size
        cpu_capacity_per_rank = cpu_capacity_bytes // world_size
        if "cpu_bytes_to_use_per_rank" in extra_config:
            explicit = int(extra_config["cpu_bytes_to_use_per_rank"])
            if explicit != cpu_capacity_per_rank:
                logger.warning(
                    "cpu_bytes_to_use_per_rank (%.2f GB) != "
                    "cpu_bytes_to_use/world_size (%.2f GB). Using per-rank value.",
                    explicit / (1024**3),
                    cpu_capacity_per_rank / (1024**3),
                )
            cpu_capacity_per_rank = explicit

        lazy_offload = bool(extra_config.get("lazy_offload", False))

        self.scheduler_manager: SimpleCPUOffloadScheduler | None = None
        self.worker_handler: SimpleCPUOffloadWorker | None = None

        if not enable_prefix_caching:
            logger.warning(
                "Detected prefix caching disabled, disabling CPU offload "
                "since it requires prefix caching."
            )
            return

        logger.info(
            "SimpleCPUOffloadConnector: role=%s, "
            "per_rank=%.2f GB, world_size=%d, mode=%s",
            role.name,
            cpu_capacity_per_rank / (1024**3),
            world_size,
            "lazy" if lazy_offload else "eager",
        )

        if role == KVConnectorRole.SCHEDULER:
            self.scheduler_manager = SimpleCPUOffloadScheduler(
                vllm_config,
                kv_cache_config,
                cpu_capacity_per_rank,
                lazy_offload=lazy_offload,
            )
        elif role == KVConnectorRole.WORKER:
            self.worker_handler = SimpleCPUOffloadWorker(
                vllm_config, kv_cache_config, cpu_capacity_per_rank
            )