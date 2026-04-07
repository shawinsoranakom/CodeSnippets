def is_cached(self, instance):
        return self.cache_name in instance._state.fields_cache