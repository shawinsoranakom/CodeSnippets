def __getattr__(self, attr):
        """Proxy to the underlying HttpRequest object."""
        return getattr(self._request, attr)