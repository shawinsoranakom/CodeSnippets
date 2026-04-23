def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.enabled:
            return
        if self.use_device and hasattr(torch, self.use_device):
            device_module = getattr(torch, self.use_device)
            if hasattr(device_module, "synchronize"):
                device_module.synchronize()

        if self._function_events and self.acc_events:
            self._old_function_events = self._function_events
        self._function_events = None
        self._needs_processing = True

        t0 = perf_counter_ns()

        self.kineto_results = _disable_profiler()
        t1 = perf_counter_ns()
        self._stats.profiler_disable_call_duration_us = int((t1 - t0) / 1000)
        self.profiling_end_time_ns = t0

        _run_on_profiler_stop()

        self._stats.profiling_window_duration_sec = (
            (self.profiling_end_time_ns - self.profiling_start_time_ns) * 1.0 / 1e9
        )

        # If we plan to accumulate events we should post process the function events
        # right away to retain the state across multiple start/stop calls
        if self.acc_events:
            self._ensure_function_events()
        return False