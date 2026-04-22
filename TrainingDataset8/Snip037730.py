def _handle_clear_cache_request(self) -> None:
        """Clear this app's cache.

        Because this cache is global, it will be cleared for all users.

        """
        legacy_caching.clear_cache()
        caching.memo.clear()
        caching.singleton.clear()
        self._session_state.clear()