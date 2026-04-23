def _remove_prefetched_objects(self):
            # Walk up the ancestor-chain (if cached) to try and find a prefetch
            # in an ancestor.
            for instance, _ in _traverse_ancestors(rel.field.model, self.instance):
                try:
                    instance._prefetched_objects_cache.pop(self.prefetch_cache_name)
                except (AttributeError, KeyError):
                    pass