def stop_watching_path(self, path: str, callback: Callable[[str], None]) -> None:
        """Stop watching a path."""
        folder_path = os.path.abspath(os.path.dirname(path))

        with self._lock:
            folder_handler = self._folder_handlers.get(folder_path)

            if folder_handler is None:
                LOGGER.debug(
                    "Cannot stop watching path, because it is already not being "
                    "watched. %s",
                    folder_path,
                )
                return

            folder_handler.remove_path_change_listener(path, callback)

            if not folder_handler.is_watching_paths():
                # Sometimes watchdog's FileSystemEventHandler does not have
                # a .watch property. It's unclear why -- may be due to a
                # race condition.
                if hasattr(folder_handler, "watch"):
                    self._observer.unschedule(folder_handler.watch)
                del self._folder_handlers[folder_path]