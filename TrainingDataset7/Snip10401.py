def deconstruct(self):
        kwargs = {
            "code": self.code,
        }
        if self.reverse_code is not None:
            kwargs["reverse_code"] = self.reverse_code
        if self.atomic is not None:
            kwargs["atomic"] = self.atomic
        if self.hints:
            kwargs["hints"] = self.hints
        if self.elidable:
            kwargs["elidable"] = self.elidable
        return (self.__class__.__qualname__, [], kwargs)