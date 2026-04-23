def __get__(self, instance, cls=None):
        return tuple(getattr(instance, attname) for attname in self.attnames)