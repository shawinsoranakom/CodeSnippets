def close_all() -> None:
        """Close the _MultiPathWatcher singleton."""
        path_watcher = _MultiPathWatcher.get_singleton()
        path_watcher.close()
        LOGGER.debug("Watcher closed")