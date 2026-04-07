def clone(self):
        """
        Uses deconstruct() to clone a new copy of this Field.
        Will not preserve any class attachments/attribute names.
        """
        name, path, args, kwargs = self.deconstruct()
        return self.__class__(*args, **kwargs)