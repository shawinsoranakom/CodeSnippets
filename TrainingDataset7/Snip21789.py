def __set__(self, instance, value):
        self._count_call(instance, "set")
        instance.__dict__[self.field.attname] = value