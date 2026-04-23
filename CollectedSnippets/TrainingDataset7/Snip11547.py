def get_prefetch_cache(self):
            # Walk up the ancestor-chain (if cached) to try and find a prefetch
            # in an ancestor.
            for instance, _ in _traverse_ancestors(rel.field.model, self.instance):
                try:
                    return instance._prefetched_objects_cache[self.prefetch_cache_name]
                except (AttributeError, KeyError):
                    pass
            return None