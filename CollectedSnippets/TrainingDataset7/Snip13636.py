def trace(self, path, secure=False, *, headers=None, query_params=None, **extra):
        """Construct a TRACE request."""
        return self.generic(
            "TRACE",
            path,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )