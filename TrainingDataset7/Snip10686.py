def clone(self):
        _, args, kwargs = self.deconstruct()
        return self.__class__(*args, **kwargs)