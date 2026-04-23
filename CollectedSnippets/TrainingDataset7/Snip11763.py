def clone(self):
        """Create a copy of this Index."""
        _, args, kwargs = self.deconstruct()
        return self.__class__(*args, **kwargs)