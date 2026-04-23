def _start_workers(self, worker_group: WorkerGroup) -> dict[int, Any]:
        spec = worker_group.spec
        store = worker_group.store
        if store is None:
            raise AssertionError
        restart_count = spec.max_restarts - self._remaining_restarts

        use_agent_store: bool = spec.rdzv_handler.use_agent_store
        logger.info("use_agent_store: %s", use_agent_store)

        args: dict[int, tuple] = {}
        envs: dict[int, dict[str, str]] = {}
        log_line_prefixes: dict[int, str] | None = (
            {} if self._log_line_prefix_template else None
        )
        for worker in worker_group.workers:
            local_rank = worker.local_rank
            worker_env = {
                "RANK": str(worker.global_rank),
                "GROUP_RANK": str(worker_group.group_rank),
                "ROLE_RANK": str(worker.role_rank),
                "ROLE_NAME": spec.role,
                "LOCAL_WORLD_SIZE": str(spec.local_world_size),
                "WORLD_SIZE": str(worker.world_size),
                "GROUP_WORLD_SIZE": str(worker_group.group_world_size),
                "ROLE_WORLD_SIZE": str(worker.role_world_size),
                "MASTER_ADDR": worker_group.master_addr,
                "MASTER_PORT": str(worker_group.master_port),
                "TORCHELASTIC_RESTART_COUNT": str(restart_count),
                "TORCHELASTIC_MAX_RESTARTS": str(spec.max_restarts),
                "TORCHELASTIC_RUN_ID": spec.rdzv_handler.get_run_id(),
                "TORCHELASTIC_USE_AGENT_STORE": str(use_agent_store),
                "TORCH_NCCL_ASYNC_ERROR_HANDLING": os.getenv(
                    "TORCH_NCCL_ASYNC_ERROR_HANDLING", str(1)
                ),
            }
            self._set_local_rank_env(worker_env, local_rank, spec)
            if "OMP_NUM_THREADS" in os.environ:
                worker_env["OMP_NUM_THREADS"] = os.environ["OMP_NUM_THREADS"]

            if self._log_line_prefix_template:
                log_line_prefix = Template(
                    self._log_line_prefix_template
                ).safe_substitute(
                    role_name=spec.role,
                    rank=worker.global_rank,
                    local_rank=local_rank,
                )
                # pyrefly: ignore [unsupported-operation]
                log_line_prefixes[local_rank] = log_line_prefix

            # pyrefly: ignore [unsupported-operation]
            envs[local_rank] = worker_env
            worker_args = list(spec.args)
            worker_args = macros.substitute(worker_args, str(local_rank))
            args[local_rank] = tuple(worker_args)

        self._setup_local_watchdog(envs=envs)
        self._setup_healthcheck()

        if spec.entrypoint is None:
            raise AssertionError
        if self._logs_specs is None:
            raise AssertionError
        self._pcontext = start_processes(
            name=spec.role,
            entrypoint=spec.entrypoint,
            args=args,
            envs=envs,
            logs_specs=self._logs_specs,
            log_line_prefixes=log_line_prefixes,
            start_method=self._start_method,
            numa_options=spec.numa_options,
            duplicate_stdout_filters=spec.duplicate_stdout_filters,
            duplicate_stderr_filters=spec.duplicate_stderr_filters,
        )

        return self._pcontext.pids()