def __next__(self):
        """Iteration interface -- return the next item in the stream"""
        raise NotImplementedError(
            "subclasses of Deserializer must provide a __next__() method"
        )