def process_request(self, request):
        """
        Check whether the page is already cached and return the cached
        version if available.
        """
        if request.method not in ("GET", "HEAD"):
            request._cache_update_cache = False
            return None  # Don't bother checking the cache.

        # try and get the cached GET response
        cache_key = get_cache_key(request, self.key_prefix, "GET", cache=self.cache)
        if cache_key is None:
            request._cache_update_cache = True
            return None  # No cache information available, need to rebuild.
        response = self.cache.get(cache_key)
        # if it wasn't found and we are looking for a HEAD, try looking just
        # for that
        if response is None and request.method == "HEAD":
            cache_key = get_cache_key(
                request, self.key_prefix, "HEAD", cache=self.cache
            )
            response = self.cache.get(cache_key)

        if response is None:
            request._cache_update_cache = True
            return None  # No cache information available, need to rebuild.

        # Derive the age estimation of the cached response.
        if (max_age_seconds := get_max_age(response)) is not None and (
            expires_timestamp := parse_http_date_safe(response["Expires"])
        ) is not None:
            now_timestamp = int(time.time())
            remaining_seconds = expires_timestamp - now_timestamp
            # Use Age: 0 if local clock got turned back.
            response["Age"] = max(0, max_age_seconds - remaining_seconds)

        # hit, return cached response
        request._cache_update_cache = False
        return response