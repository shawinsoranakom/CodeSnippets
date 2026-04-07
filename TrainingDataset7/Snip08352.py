def __eq__(self, other):
        return isinstance(other, self.__class__) and all(
            getattr(self, attr) == getattr(other, attr)
            for attr in ["level", "msg", "hint", "obj", "id"]
        )