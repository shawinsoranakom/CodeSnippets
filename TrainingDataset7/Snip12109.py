def _clear_cached_class_lookups(cls):
        for subclass in subclasses(cls):
            subclass.get_class_lookups.cache_clear()