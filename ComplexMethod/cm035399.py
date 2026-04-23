async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:  # type: ignore[override]
        try:
            async with httpx.AsyncClient(verify=httpx_verify_option()) as client:
                gitlab_headers = await self._get_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=gitlab_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    gitlab_headers = await self._get_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=gitlab_headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                if 'X-Total' in response.headers:
                    headers['X-Total'] = response.headers['X-Total']

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return response.json(), headers
                else:
                    return response.text, headers

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)