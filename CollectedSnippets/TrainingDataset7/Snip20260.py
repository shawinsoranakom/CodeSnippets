def deconstruct(self):
        kwargs = {}
        if self.kwarg1 is not None:
            kwargs["kwarg1"] = self.kwarg1
        if self.kwarg2 is not None:
            kwargs["kwarg2"] = self.kwarg2
        return (
            self.__class__.__name__,
            [self.arg1, self.arg2],
            kwargs,
        )