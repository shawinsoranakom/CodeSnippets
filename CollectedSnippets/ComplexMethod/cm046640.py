def _shutdown_subprocess(self, timeout: float = 10.0) -> None:
        """Gracefully shut down the inference subprocess."""
        self._stop_dispatcher()  # Stop dispatcher before killing subprocess
        if self._proc is None or not self._proc.is_alive():
            self._proc = None
            return

        # 1. Cancel any ongoing generation first (instant via mp.Event)
        self._cancel_generation()
        time.sleep(0.5)  # Brief wait for generation to stop

        # 2. Drain stale responses from queue
        self._drain_queue()

        # 3. Send shutdown command
        try:
            self._cmd_queue.put({"type": "shutdown"})
        except (OSError, ValueError):
            pass

        # 4. Wait for graceful shutdown
        try:
            self._proc.join(timeout = timeout)
        except Exception:
            pass

        # 5. Force kill if still alive
        if self._proc is not None and self._proc.is_alive():
            logger.warning("Inference subprocess did not exit gracefully, terminating")
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
        self._cancel_event = None
        logger.info("Inference subprocess shut down")