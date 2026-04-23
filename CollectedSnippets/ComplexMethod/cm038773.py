def step(self) -> None:
        """Update the profiler state at each worker step,
        to handle delayed starts and max iteration limits."""
        if not self._active:
            return

        self._active_iteration_count += 1

        if (
            not self._running
            and self._delay_iters > 0
            and self._active_iteration_count == self._delay_iters
        ):
            logger.info_once("Starting profiler after delay...")
            self._call_start()

        # Call profiler step for schedule-based profiling
        # Only count iterations where data is actually recorded (not warmup)
        if self._running and self._profiler_step():
            self._profiling_for_iters += 1

        if (
            self._max_iters > 0
            and self._running
            and self._profiling_for_iters > self._max_iters
        ):
            # Automatically stop the profiler after max iters
            # will be marked as not running, but leave as active so that stop
            # can clean up properly
            logger.info_once("Max profiling iterations reached. Stopping profiler...")
            self._call_stop()
            return