def __init__(self, config: "VllmConfig"):
        if not current_platform.is_cpu():
            return

        self.local_world_size = config.parallel_config.local_world_size
        self.local_dp_rank = config.parallel_config.data_parallel_rank_local
        # This is a bit tricky because the internal DP size
        # is always 1 for non-MoE models
        self.internal_dp_size = config.parallel_config._api_process_count

        self.simulate_multi_node = os.environ.get("VLLM_CPU_SIM_MULTI_NUMA", "0") != "0"
        ld_preload_str = os.getenv("LD_PRELOAD", "")
        self.use_iomp = "libiomp" in ld_preload_str or "libomp" in ld_preload_str
        self.use_gomp = "libgomp" in ld_preload_str

        assert not (self.use_iomp and self.use_gomp)

        # at least reserve 1/local_world_size(for ARM) core for scheduler
        # proc as always use MP executor
        # TODO: make scheduler proc sleep when idle
        self.reserve_cpu_num = (
            self.local_world_size
            if current_platform.get_cpu_architecture() == CpuArchEnum.ARM
            else 1
        )
        # reserve at one more core for nixl_connector under p/d case
        if config.kv_transfer_config:
            self.reserve_cpu_num += 1

        if envs.VLLM_CPU_NUM_OF_RESERVED_CPU is not None:
            if self.reserve_cpu_num > envs.VLLM_CPU_NUM_OF_RESERVED_CPU:
                msg = (
                    f"VLLM_CPU_NUM_OF_RESERVED_CPU is less than "
                    "the minimum requirement"
                    f": {self.reserve_cpu_num} cores"
                )
                logger.warning(msg=msg)
            self.reserve_cpu_num = envs.VLLM_CPU_NUM_OF_RESERVED_CPU

        self._parse_omp_threads_bind_env()

        assert not self.simulate_multi_node or self.auto_setup