def get_cached_value(self, instance, default=NOT_PROVIDED):
        try:
            return instance._state.fields_cache[self.cache_name]
        except KeyError:
            if default is NOT_PROVIDED:
                raise
            return default