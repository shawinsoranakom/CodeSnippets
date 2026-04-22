def close(self) -> None:
        """Stop watching the path corresponding to this EventBasedPathWatcher."""
        path_watcher = _MultiPathWatcher.get_singleton()
        path_watcher.stop_watching_path(self._path, self._on_changed)