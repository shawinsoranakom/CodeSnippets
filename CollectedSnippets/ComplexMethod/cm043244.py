async def _memory_monitor_task(self):
        """Background task to continuously monitor memory usage and update state"""
        while True:
            self.current_memory_percent = get_true_memory_usage_percent()

            # Enter memory pressure mode if we cross the threshold
            if self.current_memory_percent >= self.memory_threshold_percent:
                if not self.memory_pressure_mode:
                    self.memory_pressure_mode = True
                    self._high_memory_start_time = time.time()
                    if self.monitor:
                        self.monitor.update_memory_status("PRESSURE")
                else:
                    if self._high_memory_start_time is None:
                        self._high_memory_start_time = time.time()
                    if (
                        self.memory_wait_timeout is not None
                        and self._high_memory_start_time is not None
                        and time.time() - self._high_memory_start_time >= self.memory_wait_timeout
                    ):
                        raise MemoryError(
                            "Memory usage exceeded threshold for"
                            f" {self.memory_wait_timeout} seconds"
                        )

            # Exit memory pressure mode if we go below recovery threshold
            elif self.memory_pressure_mode and self.current_memory_percent <= self.recovery_threshold_percent:
                self.memory_pressure_mode = False
                self._high_memory_start_time = None
                if self.monitor:
                    self.monitor.update_memory_status("NORMAL")
            elif self.current_memory_percent < self.memory_threshold_percent:
                self._high_memory_start_time = None

            # In critical mode, we might need to take more drastic action
            if self.current_memory_percent >= self.critical_threshold_percent:
                if self.monitor:
                    self.monitor.update_memory_status("CRITICAL")
                # We could implement additional memory-saving measures here

            await asyncio.sleep(self.check_interval)