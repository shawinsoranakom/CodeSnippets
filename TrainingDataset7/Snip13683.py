async def _ahandle_redirects(
        self,
        response,
        data="",
        content_type="",
        headers=None,
        query_params=None,
        **extra,
    ):
        """
        Follow any redirects by requesting responses from the server using GET.
        """
        response.redirect_chain = []
        while response.status_code in REDIRECT_STATUS_CODES:
            redirect_chain = response.redirect_chain
            response = await self._follow_redirect(
                response,
                data=data,
                content_type=content_type,
                headers=headers,
                query_params=query_params,
                **extra,
            )
            response.redirect_chain = redirect_chain
            self._ensure_redirects_not_cyclic(response)
        return response