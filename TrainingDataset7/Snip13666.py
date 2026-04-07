def head(
        self,
        path,
        data=None,
        follow=False,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Request a response from the server using HEAD."""
        self.extra = extra
        self.headers = headers
        response = super().head(
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