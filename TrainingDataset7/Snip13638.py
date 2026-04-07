def put(
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
        """Construct a PUT request."""
        data = self._encode_json(data, content_type)
        return self.generic(
            "PUT",
            path,
            data,
            content_type,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )