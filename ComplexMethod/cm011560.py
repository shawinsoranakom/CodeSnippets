def _rendezvous(self, worker_group: WorkerGroup) -> None:
        r"""Run rendezvous for the workers specified by the worker spec.

        Assigns workers a new global rank and world size.
        Updates the rendezvous store for the worker group.
        """
        spec = worker_group.spec

        with self.record_duration("RENDEZVOUS"):
            rdzv_info = spec.rdzv_handler.next_rendezvous()
        store = rdzv_info.store
        group_rank = rdzv_info.rank
        group_world_size = rdzv_info.world_size

        # master_addr/master_port could be explicitly overridden
        # TODO: BC - specific to static rdzv and can be simplified further
        master_addr = spec.master_addr or rdzv_info.bootstrap_store_info.master_addr
        master_port = spec.master_port or rdzv_info.bootstrap_store_info.master_port

        self._store = store

        with self.record_duration("ASSIGN_WORKER_RANKS"):
            workers = self._assign_worker_ranks(
                store, group_rank, group_world_size, spec
            )
        worker_group.workers = workers
        worker_group.store = store
        worker_group.group_rank = group_rank
        worker_group.group_world_size = group_world_size
        worker_group.master_addr = master_addr
        worker_group.master_port = master_port

        restart_count = spec.max_restarts - self._remaining_restarts

        logger.info(
            "[%(role)s] Rendezvous complete for workers. Result:\n"
            "  restart_count=%(restart_count)s\n"
            "  master_addr=%(master_addr)s\n"
            "  master_port=%(master_port)s\n"
            "  group_rank=%(group_rank)s\n"
            "  group_world_size=%(group_world_size)s\n"
            "  local_ranks=%(local_ranks)s\n"
            "  role_ranks=%(role_ranks)s\n"
            "  global_ranks=%(global_ranks)s\n"
            "  role_world_sizes=%(role_world_sizes)s\n"
            "  global_world_sizes=%(global_world_sizes)s\n"
            "  event_log_handler=%(event_log_handler)s\n",
            {
                "role": spec.role,
                "restart_count": restart_count,
                "master_addr": master_addr,
                "master_port": master_port,
                "group_rank": group_rank,
                "group_world_size": group_world_size,
                "local_ranks": [worker.local_rank for worker in workers],
                "role_ranks": [worker.role_rank for worker in workers],
                "global_ranks": [worker.global_rank for worker in workers],
                "role_world_sizes": [worker.role_world_size for worker in workers],
                "global_world_sizes": [worker.world_size for worker in workers],
                "event_log_handler": spec.event_log_handler,
            },
        )