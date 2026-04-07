def __getattr__(self, attr):
        if attr == "wrapped":
            return self.__dict__.wrapped
        return getattr(self.wrapped, attr)