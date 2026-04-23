def backends(self):
        if self._backends is None:
            self._backends = settings.STORAGES.copy()
        return self._backends