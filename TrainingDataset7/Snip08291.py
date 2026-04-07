def _cache(self):
        """
        Implement transparent thread-safe access to a memcached client.
        """
        return self._class(self.client_servers, **self._options)