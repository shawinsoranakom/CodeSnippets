async def _handle_http(
        self, 
        url: str, 
        config: CrawlerRunConfig
    ) -> AsyncCrawlResponse:
        async with self._session_context() as session:
            timeout = ClientTimeout(
                total=config.page_timeout or self.DEFAULT_TIMEOUT,
                connect=10,
                sock_read=30
            )

            headers = dict(self._BASE_HEADERS)
            if self.browser_config.headers:
                headers.update(self.browser_config.headers)

            request_kwargs = {
                'timeout': timeout,
                'allow_redirects': self.browser_config.follow_redirects,
                'ssl': self.browser_config.verify_ssl,
                'headers': headers
            }

            if self.browser_config.method == "POST":
                if self.browser_config.data:
                    request_kwargs['data'] = self.browser_config.data
                if self.browser_config.json:
                    request_kwargs['json'] = self.browser_config.json

            await self.hooks['before_request'](url, request_kwargs)

            try:
                async with session.request(self.browser_config.method, url, **request_kwargs) as response:
                    content = memoryview(await response.read())

                    if not (200 <= response.status < 300):
                        raise HTTPStatusError(
                            response.status,
                            f"Unexpected status code for {url}"
                        )

                    encoding = response.charset
                    if not encoding:
                        encoding = chardet.detect(content.tobytes())['encoding'] or 'utf-8'                    

                    result = AsyncCrawlResponse(
                        html=content.tobytes().decode(encoding, errors='replace'),
                        response_headers=dict(response.headers),
                        status_code=response.status,
                        redirected_url=str(response.url)
                    )

                    await self.hooks['after_request'](result)
                    return result

            except aiohttp.ServerTimeoutError as e:
                await self.hooks['on_error'](e)
                raise ConnectionTimeoutError(f"Request timed out: {str(e)}")

            except aiohttp.ClientConnectorError as e:
                await self.hooks['on_error'](e)
                raise ConnectionError(f"Connection failed: {str(e)}")

            except aiohttp.ClientError as e:
                await self.hooks['on_error'](e)
                raise HTTPCrawlerError(f"HTTP client error: {str(e)}")

            except asyncio.exceptions.TimeoutError as e:
                await self.hooks['on_error'](e)
                raise ConnectionTimeoutError(f"Request timed out: {str(e)}")

            except Exception as e:
                await self.hooks['on_error'](e)
                raise HTTPCrawlerError(f"HTTP request failed: {str(e)}")