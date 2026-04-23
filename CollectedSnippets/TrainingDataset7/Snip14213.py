def __getitem__(self, index):
        if isinstance(index, slice) or index < 0:
            # Suboptimally consume whole iterator to handle slices and negative
            # indexes.
            return list(self)[index]
        try:
            return next(islice(self, index, index + 1))
        except StopIteration:
            raise IndexError("index out of range") from None