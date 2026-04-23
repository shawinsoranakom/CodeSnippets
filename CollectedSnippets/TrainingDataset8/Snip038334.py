def _register_watcher(self, filepath, module_name):
        global PathWatcher
        if PathWatcher is None:
            PathWatcher = get_default_path_watcher_class()

        if PathWatcher is NoOpPathWatcher:
            return

        try:
            wm = WatchedModule(
                watcher=PathWatcher(filepath, self.on_file_changed),
                module_name=module_name,
            )
        except PermissionError:
            # If you don't have permission to read this file, don't even add it
            # to watchers.
            return

        self._watched_modules[filepath] = wm