def deconstruct(self):
        kwargs = {
            "name": self.name,
            "table": self.table,
        }
        return (self.__class__.__qualname__, [], kwargs)