def __getstate__(self):
        state = self.__dict__.copy()
        # Weak references can't be pickled.
        state.pop("peers", None)
        return state