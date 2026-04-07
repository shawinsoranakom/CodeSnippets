def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self.field.name)
        self.field.set_cached_value(instance, value)
        if value is not None and not self.field.remote_field.multiple:
            self.field.remote_field.set_cached_value(value, instance)