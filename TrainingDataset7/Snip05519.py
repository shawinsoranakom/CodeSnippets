def __dir__(self):
        return sorted(
            s
            for s in [*self.__dict__, *dir(self.default_settings)]
            if s not in self._deleted
        )