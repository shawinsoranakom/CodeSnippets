async def match_request(
        self,
        method,
        url,
        *,
        data=None,
        auth=None,
        params=None,
        headers=None,
        allow_redirects=None,
        timeout=None,
        json=None,
        cookies=None,
        **kwargs,
    ):
        """Match a request against pre-registered requests."""
        data = data or json
        url = URL(url)
        if params:
            url = url.with_query(params)

        for response in self._mocks:
            if response.match_request(method, url, params):
                # If auth is provided, try to encode it to trigger any encoding errors
                if auth is not None:
                    auth.encode()
                self.mock_calls.append((method, url, data, headers))
                if response.side_effect:
                    response = await response.side_effect(method, url, data)
                if response.exc:
                    raise response.exc
                return response

        raise AssertionError(f"No mock registered for {method.upper()} {url} {params}")