def post(
        self,
        path,
        data=None,
        content_type=MULTIPART_CONTENT,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Construct a POST request."""
        data = self._encode_json({} if data is None else data, content_type)
        post_data = self._encode_data(data, content_type)

        return self.generic(
            "POST",
            path,
            post_data,
            content_type,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )