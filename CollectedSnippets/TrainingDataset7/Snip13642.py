def _base_scope(self, **request):
        """The base scope for a request."""
        # This is a minimal valid ASGI scope, plus:
        # - headers['cookie'] for cookie support,
        # - 'client' often useful, see #8551.
        scope = {
            "asgi": {"version": "3.0"},
            "type": "http",
            "http_version": "1.1",
            "client": ["127.0.0.1", 0],
            "server": ("testserver", "80"),
            "scheme": "http",
            "method": "GET",
            "headers": [],
            **self.defaults,
            **request,
        }
        scope["headers"].append(
            (
                b"cookie",
                b"; ".join(
                    sorted(
                        ("%s=%s" % (morsel.key, morsel.coded_value)).encode("ascii")
                        for morsel in self.cookies.values()
                    )
                ),
            )
        )
        return scope