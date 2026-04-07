def __copy__(self):
        return self.__class__([(k, v[:]) for k, v in self.lists()])