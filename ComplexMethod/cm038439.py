def _staged_barrier(self, use_new_group: bool, barrier_name: str) -> bool:
        """
        Execute a two-staged barrier to synchronize all engines in the DP group.

        Some DP EngineCores may receive the reconfiguration notifications
        later than others, and already proceed to engine step (model forward)
        in the busy loop.
        In this case, EngineCores that already proceed to reconfiguration
        should skip reconfiguration and execute model forward for one more
        step, so in the next step, all EngineCores will be synchronized.
        We use a two-staged barrier to achieve this. The first time each
        EngineCore executes the barrier, if a timeout is reached before the
        barrier completes, that means some EngineCores have already entered
        engine step. The EngineCores that timed out will then proceed to
        engine step, and will synchronize with the other EngineCores in the
        next step with a barrier without timeout.
        """
        dp_group = self.new_dp_group if use_new_group else self.old_dp_group
        dp_store = self.new_dp_store if use_new_group else self.old_dp_store
        assert dp_group is not None and dp_store is not None

        group_rank = dp_group.rank()
        group_size = dp_group.size()
        barrier_id = f"eep_barrier_{barrier_name}"
        sync_key = f"{barrier_id}_sync"

        # TODO(yongji): figure out appropriate timeout for the barrier
        timeout = None if dp_store.check([sync_key]) else timedelta(seconds=5)

        try:
            self._execute_tcp_store_barrier(
                dp_store, group_rank, group_size, barrier_id, timeout=timeout
            )
            torch.distributed.barrier(dp_group)
            if group_rank == 0:
                dp_store.delete_key(sync_key)
                for i in range(group_size):
                    dp_store.delete_key(f"arrival_{barrier_id}_{i}")
            return True
        except _BarrierTimeoutError as e:
            if timeout is None:
                raise RuntimeError("Unexpected timeout encountered") from e
            dp_store.compare_set(sync_key, "", b"1")
            return False