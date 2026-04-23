def get(
        self, path, data=None, secure=False, *, headers=None, query_params=None, **extra
    ):
        """Construct a GET request."""
        if query_params and data:
            raise ValueError("query_params and data arguments are mutually exclusive.")
        query_params = data or query_params
        query_params = {} if query_params is None else query_params
        return self.generic(
            "GET",
            path,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )