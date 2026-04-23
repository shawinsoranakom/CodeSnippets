def __reduce__(self):
        # tblib 3.2+ makes exception subclasses picklable by default.
        # Return (cls, ()) so the constructor fails on unpickle, preserving
        # the needed behavior for test_pickle_errors_detection.
        return (self.__class__, ())