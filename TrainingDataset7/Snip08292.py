def get_backend_timeout(self, timeout=DEFAULT_TIMEOUT):
        """
        Memcached deals with long (> 30 days) timeouts in a special
        way. Call this function to obtain a safe value for your timeout.
        """
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout

        if timeout is None:
            # Using 0 in memcache sets a non-expiring timeout.
            return 0
        elif int(timeout) == 0:
            # Other cache backends treat 0 as set-and-expire. To achieve this
            # in memcache backends, a negative timeout must be passed.
            timeout = -1

        if timeout > 2592000:  # 60*60*24*30, 30 days
            # See:
            # https://github.com/memcached/memcached/wiki/Programming#expiration
            # "Expiration times can be set from 0, meaning "never expire", to
            # 30 days. Any time higher than 30 days is interpreted as a Unix
            # timestamp date. If you want to expire an object on January 1st of
            # next year, this is how you do that."
            #
            # This means that we have to switch to absolute timestamps.
            timeout += int(time.time())
        return int(timeout)