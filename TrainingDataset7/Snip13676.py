async def post(
        self,
        path,
        data=None,
        content_type=MULTIPART_CONTENT,
        follow=False,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Request a response from the server using POST."""
        self.extra = extra
        self.headers = headers
        response = await super().post(
            path,
            data=data,
            content_type=content_type,
            secure=secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )
        if follow:
            response = await self._ahandle_redirects(
                response,
                data=data,
                content_type=content_type,
                headers=headers,
                query_params=query_params,
                **extra,
            )
        return response