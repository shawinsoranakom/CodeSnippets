def __init__(
        self, verbose_name=None, name=None, upload_to="", storage=None, **kwargs
    ):
        self._primary_key_set_explicitly = "primary_key" in kwargs

        self.storage = storage if storage is not None else default_storage
        if callable(self.storage):
            # Hold a reference to the callable for deconstruct().
            self._storage_callable = self.storage
            self.storage = self.storage()
            if not isinstance(self.storage, Storage):
                raise TypeError(
                    "%s.storage must be a subclass/instance of %s.%s"
                    % (
                        self.__class__.__qualname__,
                        Storage.__module__,
                        Storage.__qualname__,
                    )
                )
        self.upload_to = upload_to

        kwargs.setdefault("max_length", 100)
        super().__init__(verbose_name, name, **kwargs)