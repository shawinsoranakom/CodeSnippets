def _close(self, death_sig: signal.Signals, timeout: int = 30) -> None:
        if not self._pc:
            return
        for proc in self._pc.processes:
            if proc.is_alive():
                logger.warning(
                    "Closing process %s via signal %s", proc.pid, death_sig.name
                )
                try:
                    os.kill(proc.pid, death_sig)
                except ProcessLookupError:
                    # If the process exited because of some reason,
                    # `ProcessLookupError` will be raised, it is safe to ignore it.
                    pass
        end = time.monotonic() + timeout
        for proc in self._pc.processes:
            time_to_wait = end - time.monotonic()
            if time_to_wait <= 0:
                break
            proc.join(time_to_wait)
        for proc in self._pc.processes:
            if proc.is_alive():
                logger.warning(
                    "Unable to shutdown process %s via %s, forcefully exiting via %s",
                    proc.pid,
                    death_sig,
                    _get_kill_signal(),
                )
                try:
                    os.kill(proc.pid, _get_kill_signal())
                except ProcessLookupError:
                    # If the process exited because of some reason,
                    # `ProcessLookupError` will be raised, it is safe to ignore it.
                    pass
            proc.join()