def _execute_tcp_store_barrier(
        self, dp_store, group_rank, group_size, barrier_id, timeout=None
    ):
        arrival_key = f"arrival_{barrier_id}_{group_rank}"
        dp_store.set(arrival_key, b"1")

        start_time = time.time()
        processes_arrived: set[int] = set()

        while len(processes_arrived) < group_size:
            if (
                timeout is not None
                and time.time() - start_time > timeout.total_seconds()
            ):
                raise _BarrierTimeoutError(
                    f"Barrier timed out after {timeout.total_seconds()} seconds"
                )

            for i in range(group_size):
                if i in processes_arrived:
                    continue

                key = f"arrival_{barrier_id}_{i}"
                present = dp_store.check([key])
                if present:
                    processes_arrived.add(i)

            if len(processes_arrived) < group_size:
                sched_yield()