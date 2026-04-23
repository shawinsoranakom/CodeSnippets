def __new__(cls) -> "_MultiPathWatcher":
        """Constructor."""
        if _MultiPathWatcher._singleton is not None:
            raise RuntimeError("Use .get_singleton() instead")
        return super(_MultiPathWatcher, cls).__new__(cls)