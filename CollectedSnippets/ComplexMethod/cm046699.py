def is_training_active(self) -> bool:
        """Check if training is currently active."""
        with self._lock:
            # Subprocess alive = active
            if self._proc is not None and self._proc.is_alive():
                return True

            # Stop was requested and process exited → inactive
            if self._should_stop:
                return False

            # Check progress state
            p = self._progress
            if p.is_training:
                return True
            if p.is_completed or p.error:
                return False

            # Check status message for activity indicators
            status_lower = (p.status_message or "").lower()
            if any(
                k in status_lower
                for k in [
                    "cancelled",
                    "canceled",
                    "stopped",
                    "completed",
                    "ready to train",
                ]
            ):
                return False
            if any(
                k in status_lower
                for k in [
                    "loading",
                    "preparing",
                    "training",
                    "configuring",
                    "tokenizing",
                    "starting",
                    "importing",
                ]
            ):
                return True

            return False