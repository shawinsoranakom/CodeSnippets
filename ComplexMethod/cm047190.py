def stop_workers_gracefully(self):
        _logger.info("Stopping workers gracefully")

        if self.long_polling_pid is not None:
            # FIXME make longpolling process handle SIGTERM correctly
            self.worker_kill(self.long_polling_pid, signal.SIGKILL)
            self.long_polling_pid = None

        # Signal workers to finish their current workload then stop
        for pid in self.workers:
            self.worker_kill(pid, signal.SIGINT)

        is_main_server = self.pid == os.getpid()  # False if server reload, cannot reap children -> use psutil
        if not is_main_server:
            processes = {}
            for pid in self.workers:
                with contextlib.suppress(psutil.NoSuchProcess):
                    processes[pid] = psutil.Process(pid)

        self.beat = 0.1
        while self.workers:
            try:
                self.process_signals()
            except KeyboardInterrupt:
                _logger.info("Forced shutdown.")
                break

            if is_main_server:
                self.process_zombie()
            else:
                for pid, proc in list(processes.items()):
                    if not proc.is_running():
                        self.worker_pop(pid)
                        processes.pop(pid)

            self.sleep()
            self.process_timeout()