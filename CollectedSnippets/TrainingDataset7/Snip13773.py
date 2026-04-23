def shuffle_seed(self):
        if self._shuffler is None:
            return None
        return self._shuffler.seed