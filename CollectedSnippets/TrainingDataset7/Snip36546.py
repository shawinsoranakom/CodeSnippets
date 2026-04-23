def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        for attr in ["bar", "baz", "quux"]:
            if hasattr(self, attr) != hasattr(other, attr):
                return False
            elif getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True