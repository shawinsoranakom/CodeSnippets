def __getattribute__(self, name):
        if name == "_wrapped":
            # Avoid recursion when getting wrapped object.
            return super().__getattribute__(name)
        value = super().__getattribute__(name)
        # If attribute is a proxy method, raise an AttributeError to call
        # __getattr__() and use the wrapped object method.
        if not getattr(value, "_mask_wrapped", True):
            raise AttributeError
        return value