def _should_update_cache(self, request, response):
        return hasattr(request, "_cache_update_cache") and request._cache_update_cache