def __get__(self, instance, cls=None):
        if instance is None:
            raise AttributeError("Instance only")
        return 1