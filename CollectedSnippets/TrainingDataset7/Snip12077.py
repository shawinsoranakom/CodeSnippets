def subclasses(cls):
    yield cls
    for subclass in cls.__subclasses__():
        yield from subclasses(subclass)