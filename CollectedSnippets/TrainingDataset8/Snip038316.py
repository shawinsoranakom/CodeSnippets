def close(self) -> None:
        with self._lock:
            """Close this _MultiPathWatcher object forever."""
            if len(self._folder_handlers) != 0:
                self._folder_handlers = {}
                LOGGER.debug(
                    "Stopping observer thread even though there is a non-zero "
                    "number of event observers!"
                )
            else:
                LOGGER.debug("Stopping observer thread")

            self._observer.stop()
            self._observer.join(timeout=5)