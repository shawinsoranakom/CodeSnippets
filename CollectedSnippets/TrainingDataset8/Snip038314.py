def watch_path(
        self,
        path: str,
        callback: Callable[[str], None],
        *,  # keyword-only arguments:
        glob_pattern: Optional[str] = None,
        allow_nonexistent: bool = False,
    ) -> None:
        """Start watching a path."""
        folder_path = os.path.abspath(os.path.dirname(path))

        with self._lock:
            folder_handler = self._folder_handlers.get(folder_path)

            if folder_handler is None:
                folder_handler = _FolderEventHandler()
                self._folder_handlers[folder_path] = folder_handler

                folder_handler.watch = self._observer.schedule(
                    folder_handler, folder_path, recursive=True
                )

            folder_handler.add_path_change_listener(
                path,
                callback,
                glob_pattern=glob_pattern,
                allow_nonexistent=allow_nonexistent,
            )