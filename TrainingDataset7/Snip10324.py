def deconstruct(self):
        kwargs = {
            "name": self.name,
            "options": self.options,
        }
        return (self.__class__.__qualname__, [], kwargs)