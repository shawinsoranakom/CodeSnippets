def __copy__(self):
        duplicate = BaseContext()
        duplicate.__class__ = self.__class__
        duplicate.__dict__ = copy(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate