def _add_to_cache(self, using, ct):
        """Insert a ContentType into the cache."""
        # Note it's possible for ContentType objects to be stale; model_class()
        # will return None. Hence, there is no reliance on
        # model._meta.app_label here, just using the model fields instead.
        key = (ct.app_label, ct.model)
        self._cache.setdefault(using, {})[key] = ct
        self._cache.setdefault(using, {})[ct.id] = ct