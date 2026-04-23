def close(self):
        for wm in self._watched_modules.values():
            wm.watcher.close()
        self._watched_modules = {}
        self._is_closed = True