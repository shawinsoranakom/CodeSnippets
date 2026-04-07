def __setattr__(self, name, value):
        self._deleted.discard(name)
        super().__setattr__(name, value)