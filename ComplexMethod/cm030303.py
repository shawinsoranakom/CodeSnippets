def _force_shutdown(self, operation):
        """Attempts to terminate or kill the executor's workers based off the
        given operation. Iterates through all of the current processes and
        performs the relevant task if the process is still alive.

        After terminating workers, the pool will be in a broken state
        and no longer usable (for instance, new tasks should not be
        submitted).
        """
        if operation not in _SHUTDOWN_CALLBACK_OPERATION:
            raise ValueError(f"Unsupported operation: {operation!r}")

        processes = {}
        if self._processes:
            processes = self._processes.copy()

        # shutdown will invalidate ._processes, so we copy it right before
        # calling. If we waited here, we would deadlock if a process decides not
        # to exit.
        self.shutdown(wait=False, cancel_futures=True)

        if not processes:
            return

        for proc in processes.values():
            try:
                if not proc.is_alive():
                    continue
            except ValueError:
                # The process is already exited/closed out.
                continue

            try:
                if operation == _TERMINATE:
                    proc.terminate()
                elif operation == _KILL:
                    proc.kill()
            except ProcessLookupError:
                # The process just ended before our signal
                continue