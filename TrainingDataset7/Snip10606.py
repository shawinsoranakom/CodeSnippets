def __get__(self, instance, cls=None):
        if instance is None:
            return self
        res = instance.fetch_mode = FETCH_ONE
        return res