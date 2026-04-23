def delete(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        follow=False,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Send a DELETE request to the server."""
        self.extra = extra
        self.headers = headers
        response = super().delete(
            path,
            data=data,
            content_type=content_type,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )
        if follow:
            response = self._handle_redirects(
                response,
                data=data,
                content_type=content_type,
                headers=headers,
                query_params=query_params,
                **extra,
            )
        return response