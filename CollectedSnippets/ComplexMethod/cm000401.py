def refresh(self) -> bool:
        """Refresh lock TTL if we still own it.

        Rate limited to at most once every timeout/10 seconds (minimum 1 second).
        During rate limiting, still verifies lock existence but skips TTL extension.
        Setting _last_refresh to 0 bypasses rate limiting for testing.

        Thread-safe: uses _refresh_lock to protect _last_refresh access.
        """
        # Calculate refresh interval: max(timeout // 10, 1)
        refresh_interval = max(self.timeout // 10, 1)
        current_time = time.time()

        # Check if we're within the rate limit period (thread-safe read)
        # _last_refresh == 0 forces a refresh (bypasses rate limiting for testing)
        with self._refresh_lock:
            last_refresh = self._last_refresh
        is_rate_limited = (
            last_refresh > 0 and (current_time - last_refresh) < refresh_interval
        )

        try:
            # Always verify lock existence, even during rate limiting
            current_value = self.redis.get(self.key)
            if not current_value:
                with self._refresh_lock:
                    self._last_refresh = 0
                return False

            stored_owner = (
                current_value.decode("utf-8")
                if isinstance(current_value, bytes)
                else str(current_value)
            )
            if stored_owner != self.owner_id:
                with self._refresh_lock:
                    self._last_refresh = 0
                return False

            # If rate limited, return True but don't update TTL or timestamp
            if is_rate_limited:
                return True

            # Perform actual refresh
            if self.redis.expire(self.key, self.timeout):
                with self._refresh_lock:
                    self._last_refresh = current_time
                return True

            with self._refresh_lock:
                self._last_refresh = 0
            return False

        except Exception as e:
            logger.error(f"ClusterLock.refresh failed for key {self.key}: {e}")
            with self._refresh_lock:
                self._last_refresh = 0
            return False