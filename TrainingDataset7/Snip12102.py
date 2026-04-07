def __get__(self, instance, owner):
        if instance is None:
            return functools.partial(self.class_method, owner)
        return functools.partial(self.instance_method, instance)