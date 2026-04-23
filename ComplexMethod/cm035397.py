async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        try:
            async with httpx.AsyncClient(verify=httpx_verify_option()) as client:
                headers = await self._get_headers()
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=headers,
                    params=params,
                    method=method,
                )

                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    headers = await self._get_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                headers_out: dict[str, str] = {}
                for header in ('Link', 'X-Total-Count', 'X-Total'):
                    if header in response.headers:
                        headers_out[header] = response.headers[header]

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return response.json(), headers_out
                return response.text, headers_out

        except httpx.HTTPStatusError as err:
            raise self.handle_http_status_error(err)
        except httpx.HTTPError as err:
            raise self.handle_http_error(err)