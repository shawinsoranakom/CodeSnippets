def __set__(self, instance, value):
        instance.__dict__[self.field.attname] = value