async def options(
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
        """Request a response from the server using OPTIONS."""
        self.extra = extra
        self.headers = headers
        response = await super().options(
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