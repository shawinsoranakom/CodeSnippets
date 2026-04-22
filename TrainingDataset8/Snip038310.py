def get_singleton(cls) -> "_MultiPathWatcher":
        """Return the singleton _MultiPathWatcher object.

        Instantiates one if necessary.
        """
        if cls._singleton is None:
            LOGGER.debug("No singleton. Registering one.")
            _MultiPathWatcher()

        return cast("_MultiPathWatcher", _MultiPathWatcher._singleton)