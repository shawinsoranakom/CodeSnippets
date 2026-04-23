def _callCleanup(self, function, *args, **kwargs):
        self._callMaybeAsync(function, *args, **kwargs)