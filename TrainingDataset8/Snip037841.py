def get_function_cache(self, function_key: str) -> Cache:
        return _singleton_caches.get_cache(
            key=function_key,
            display_name=self.display_name,
            allow_widgets=self.allow_widgets,
        )