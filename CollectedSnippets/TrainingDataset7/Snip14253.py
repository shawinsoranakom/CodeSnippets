def __repr__(self):
        data = repr(list(self.dict)) if self.dict else ""
        return f"{self.__class__.__qualname__}({data})"