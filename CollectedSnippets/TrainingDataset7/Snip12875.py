def __repr__(self):
        if self.method is None or not self.get_full_path():
            return "<%s>" % self.__class__.__name__
        return "<%s: %s %r>" % (
            self.__class__.__name__,
            self.method,
            self.get_full_path(),
        )