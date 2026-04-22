def serialize(self, v: object) -> int:
        if len(self.options) == 0:
            return 0
        return index_(self.options, v)