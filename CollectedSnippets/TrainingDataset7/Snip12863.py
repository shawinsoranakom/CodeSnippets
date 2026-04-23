def __next__(self):
        try:
            return LazyStream(BoundaryIter(self._stream, self._boundary))
        except InputStreamExhausted:
            raise StopIteration()