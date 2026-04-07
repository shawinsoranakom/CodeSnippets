def __getstate__(self):
        raise pickle.PickleError("cannot be pickled for testing reasons")