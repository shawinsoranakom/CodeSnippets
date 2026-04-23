def __init__(
        self,
        local_engine_count: int,
        start_index: int,
        local_start_index: int,
        vllm_config: VllmConfig,
        local_client: bool,
        handshake_address: str,
        executor_class: type[Executor],
        log_stats: bool,
        client_handshake_address: str | None = None,
        tensor_queue: Queue | None = None,
    ):
        context = get_mp_context()
        common_kwargs = {
            "vllm_config": vllm_config,
            "local_client": local_client,
            "handshake_address": handshake_address,
            "executor_class": executor_class,
            "log_stats": log_stats,
            "tensor_queue": tensor_queue,
        }

        if client_handshake_address:
            common_kwargs["client_handshake_address"] = client_handshake_address

        is_dp = vllm_config.parallel_config.data_parallel_size > 1

        from vllm.v1.engine.core import EngineCoreProc

        self.processes: list[BaseProcess] = []
        local_dp_ranks = []
        for index in range(local_engine_count):
            local_index = local_start_index + index
            global_index = start_index + index

            # Start EngineCore in background process.
            local_dp_ranks.append(local_index)
            self.processes.append(
                context.Process(
                    target=EngineCoreProc.run_engine_core,
                    name=f"EngineCore_DP{global_index}" if is_dp else "EngineCore",
                    kwargs=common_kwargs
                    | {"dp_rank": global_index, "local_dp_rank": local_index},
                )
            )

        self._finalizer = weakref.finalize(self, shutdown, self.processes)
        self.manager_stopped = threading.Event()
        self.failed_proc_name: str | None = None

        try:
            for proc, local_dp_rank in zip(self.processes, local_dp_ranks):
                # Adjust device control in DP for non-CUDA platforms
                # as well as external and ray launchers
                # For CUDA platforms, we use torch.accelerator.set_device_index()()
                device_control_context: contextlib.AbstractContextManager[None] = (
                    contextlib.nullcontext()
                )
                if is_dp and (
                    not current_platform.is_cuda_alike()
                    or vllm_config.parallel_config.use_ray
                ):
                    device_control_context = set_device_control_env_var(
                        vllm_config, local_dp_rank
                    )

                with (
                    device_control_context,
                    numa_utils.configure_subprocess(
                        # EngineCore itself does not have a TP/PP-local rank.
                        # When DP is enabled, set_device_control_env_var()
                        # narrows visible devices to this DP shard first, so
                        # local_rank=0 means "the first local GPU in this
                        # shard". The actual TP/PP worker processes spawned by
                        # the executor are bound separately with their own
                        # local_rank values.
                        vllm_config,
                        local_rank=0,
                        dp_local_rank=local_dp_rank,
                        process_kind="EngineCore",
                    ),
                ):
                    proc.start()
        finally:
            # Kill other procs if not all are running.
            if self.finished_procs():
                self.shutdown()