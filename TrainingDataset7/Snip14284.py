def __repr__(self):
        return repr({key: value for key, value in self._store.values()})