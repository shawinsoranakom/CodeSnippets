def remove_path_change_listener(
        self, path: str, callback: Callable[[str], None]
    ) -> None:
        """Remove a path from this object's event filter."""
        with self._lock:
            watched_path = self._watched_paths.get(path, None)
            if watched_path is None:
                return

            watched_path.on_changed.disconnect(callback)
            if not watched_path.on_changed.has_receivers_for(ANY):
                del self._watched_paths[path]