def close_all() -> None:
        """Close top-level watcher object.

        This is a no-op, and exists for interface parity with
        EventBasedPathWatcher.
        """
        LOGGER.debug("Watcher closed")