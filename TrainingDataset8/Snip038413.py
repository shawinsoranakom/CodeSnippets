def initialize_storage(cls, storage: MemoryMediaFileStorage) -> None:
        """Set the MemoryMediaFileStorage object used by instances of this
        handler. Must be called on server startup.
        """
        # This is a class method, rather than an instance method, because
        # `get_content()` is a class method and needs to access the storage
        # instance.
        cls._storage = storage