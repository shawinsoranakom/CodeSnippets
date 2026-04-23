def get_function_cache(self, function_key: str) -> Cache:
        return _memo_caches.get_cache(
            key=function_key,
            persist=self.persist,
            max_entries=self.max_entries,
            ttl=self.ttl,
            display_name=self.display_name,
            allow_widgets=self.allow_widgets,
        )