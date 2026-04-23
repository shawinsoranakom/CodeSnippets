def _get_request_cache(self, method="GET", query_string=None, update_cache=None):
        request = self._get_request(
            self.host, self.path, method, query_string=query_string
        )
        request._cache_update_cache = update_cache if update_cache else True
        return request