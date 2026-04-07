def set_cached_value(self, instance, value):
        instance._state.fields_cache[self.cache_name] = value