def readline(self, size=-1, /):
        if not self.read_started:
            self.__content.seek(0)
            self.read_started = True
        if size == -1 or size is None:
            size = self.__len
        assert (
            self.__len >= size
        ), "Cannot read more than the available bytes from the HTTP incoming data."
        content = self.__content.readline(size)
        self.__len -= len(content)
        return content