def options(
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
        "Construct an OPTIONS request."
        return self.generic(
            "OPTIONS",
            path,
            data,
            content_type,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )