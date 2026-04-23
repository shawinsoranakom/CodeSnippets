def _add_default_callbacks(self, add_history, add_progbar):
        """Adds `Callback`s that are always present."""
        self._progbar = None
        self._history = None

        for cb in self.callbacks:
            if isinstance(cb, ProgbarLogger):
                self._progbar = cb
            elif isinstance(cb, History):
                self._history = cb

        if self._history is None and add_history:
            self._history = History()
            self.callbacks.append(self._history)

        if self._progbar is None and add_progbar:
            self._progbar = ProgbarLogger()
            self.callbacks.append(self._progbar)