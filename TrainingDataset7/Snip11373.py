def delete_cached_value(self, instance):
        del instance._state.fields_cache[self.cache_name]