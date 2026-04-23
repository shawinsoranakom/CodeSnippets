def _run_watchdog(self, fd: io.TextIOWrapper) -> None:
        timer_requests = self._get_requests(fd, self._max_interval)
        self.register_timers(timer_requests)
        now = time.time()
        reaped_worker_pids = set()
        kill_process = False
        reap_signal = 0

        all_expired_timers = self.get_expired_timers(now)
        log_debug_info_for_expired_timers(
            self._run_id,
            {
                pid: [expired_timer.to_json() for expired_timer in expired_timers]
                for pid, expired_timers in all_expired_timers.items()
            },
        )

        for worker_pid, expired_timers in all_expired_timers.items():
            logger.info(
                "Reaping worker_pid=[%s]. Expired timers: %s",
                worker_pid,
                self._get_scopes(expired_timers),
            )
            reaped_worker_pids.add(worker_pid)
            # In case we have multiple expired timers, we find the first timer
            # with a valid signal (>0) in the expiration time order.
            expired_timers.sort(key=lambda timer: timer.expiration_time)
            signal = 0
            expired_timer = None
            for timer in expired_timers:
                self._log_event("timer expired", timer)
                if timer.signal > 0:
                    signal = timer.signal
                    expired_timer = timer
                    break
            if signal <= 0:
                logger.info(
                    "No signal specified with worker=[%s]. Do not reap it.", worker_pid
                )
                continue
            if self._reap_worker(worker_pid, signal):
                logger.info(
                    "Successfully reaped worker=[%s] with signal=%s", worker_pid, signal
                )
                self._log_event("kill worker process", expired_timer)
                kill_process = True
                reap_signal = signal
            else:
                logger.error(
                    "Error reaping worker=[%s]. Will retry on next watchdog.",
                    worker_pid,
                )
        if kill_process and reap_signal > 0:
            logger.info(
                "Terminating the server process=[%s] because of expired timers",
                os.getpid(),
            )
            self._reap_worker(os.getpid(), reap_signal)

        self.clear_timers(reaped_worker_pids)