def __get__(self, instance, cls=None):
        return self.fget(cls)