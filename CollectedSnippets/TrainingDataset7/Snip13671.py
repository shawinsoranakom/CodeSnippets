def trace(
        self,
        path,
        data="",
        follow=False,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Send a TRACE request to the server."""
        self.extra = extra
        self.headers = headers
        response = super().trace(
            path,
            data=data,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )
        if follow:
            response = self._handle_redirects(
                response, data=data, headers=headers, query_params=query_params, **extra
            )
        return response