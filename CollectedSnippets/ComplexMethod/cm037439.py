def monitor_engine_liveness(self) -> None:
        """Monitor engine core process liveness."""

        sentinel_to_proc = {proc.sentinel: proc for proc in self.processes}
        sentinels = set(sentinel_to_proc.keys())

        while sentinels and not self.manager_stopped.is_set():
            died_sentinels = connection.wait(sentinels, timeout=1)

            for sentinel in died_sentinels:
                proc = sentinel_to_proc.pop(cast(int, sentinel))
                exitcode = proc.exitcode
                if exitcode != 0 and not self.manager_stopped.is_set():
                    self.failed_proc_name = proc.name
            if died_sentinels:
                # Any engine exit currently triggers a shutdown. Future
                # work (e.g., Elastic and fault-tolerant EP) will add finer-grained
                # handling for different exit scenarios.
                break

        self.shutdown()