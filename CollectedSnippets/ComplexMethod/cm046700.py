def _pump_loop(self) -> None:
        """Background thread: consume events from subprocess → update state."""
        while True:
            if self._proc is None or self._event_queue is None:
                return

            # Try to read an event
            event = self._read_queue(self._event_queue, timeout_sec = 0.25)
            if event is not None:
                self._handle_event(event)
                continue

            # No event — check if process is still alive
            if self._proc.is_alive():
                continue

            # Process exited — drain remaining events
            for e in self._drain_queue(self._event_queue):
                self._handle_event(e)

            # Mark as done if no explicit complete/error was received
            with self._lock:
                if self._progress.is_training:
                    if self._should_stop:
                        self._progress.is_training = False
                        self._progress.status_message = "Training stopped."
                    else:
                        self._progress.is_training = False
                        self._progress.error = (
                            self._progress.error
                            or "Training process exited unexpectedly"
                        )

            self._ensure_db_run_created()
            self._finalize_run_in_db(
                status = "stopped" if self._should_stop else "error",
                error_message = None
                if self._should_stop
                else "Training process terminated unexpectedly",
            )
            return