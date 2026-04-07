def patch(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Construct a PATCH request."""
        data = self._encode_json(data, content_type)
        return self.generic(
            "PATCH",
            path,
            data,
            content_type,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )