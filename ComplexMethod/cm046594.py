def _shutdown_subprocess(self, timeout: float = 10.0) -> None:
        """Gracefully shut down the export subprocess."""
        if self._proc is None or not self._proc.is_alive():
            self._proc = None
            return

        # 1. Drain stale responses
        self._drain_queue()

        # 2. Send shutdown command
        try:
            self._cmd_queue.put({"type": "shutdown"})
        except (OSError, ValueError):
            pass

        # 3. Wait for graceful shutdown
        try:
            self._proc.join(timeout = timeout)
        except Exception:
            pass

        # 4. Force kill if still alive
        if self._proc is not None and self._proc.is_alive():
            logger.warning("Export subprocess did not exit gracefully, terminating")
            try:
                self._proc.terminate()
                self._proc.join(timeout = 5)
            except Exception:
                pass
            if self._proc is not None and self._proc.is_alive():
                logger.warning("Subprocess still alive after terminate, killing")
                try:
                    self._proc.kill()
                    self._proc.join(timeout = 3)
                except Exception:
                    pass

        self._proc = None
        self._cmd_queue = None
        self._resp_queue = None
        logger.info("Export subprocess shut down")