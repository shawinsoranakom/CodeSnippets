def __iter__(self):
        for obj in self.stream:
            yield from self._handle_object(obj)