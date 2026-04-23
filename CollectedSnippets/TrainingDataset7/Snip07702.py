def __init__(self, *args, **kwargs):
        if "default_bounds" in kwargs:
            raise TypeError(
                f"Cannot use 'default_bounds' with {self.__class__.__name__}."
            )
        # Initializing base_field here ensures that its model matches the model
        # for self.
        if hasattr(self, "base_field"):
            self.base_field = self.base_field()
        super().__init__(*args, **kwargs)