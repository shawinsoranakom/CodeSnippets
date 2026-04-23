def __copy__(self):
        result = self.__class__("", mutable=True, encoding=self.encoding)
        for key, value in self.lists():
            result.setlist(key, value)
        return result