def deconstruct(self):
        kwargs = {
            "name": self.name,
        }
        return (self.__class__.__qualname__, [], kwargs)