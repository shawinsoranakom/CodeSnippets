def instance(cls) -> "Runtime":
        """Return the singleton Runtime instance. Raise an Error if the
        Runtime hasn't been created yet.
        """
        if cls._instance is None:
            raise RuntimeError("Runtime hasn't been created!")
        return cls._instance