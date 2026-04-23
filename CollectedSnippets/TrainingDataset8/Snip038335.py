def _deregister_watcher(self, filepath):
        if filepath not in self._watched_modules:
            return

        if filepath == self._main_script_path:
            return

        wm = self._watched_modules[filepath]
        wm.watcher.close()
        del self._watched_modules[filepath]