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

            # Add proxy support - use config.proxy_config (set by arun() from rotation strategy or direct config)
            proxy_url = None
            if config.proxy_config:
                proxy_url = self._format_proxy_url(config.proxy_config)
                request_kwargs['proxy'] = proxy_url

            if self.browser_config.method == "POST":
                if self.browser_config.data:
                    request_kwargs['data'] = self.browser_config.data
                if self.browser_config.json:
                    request_kwargs['json'] = self.browser_config.json

            await self.hooks['before_request'](url, request_kwargs)

            try:
                async with session.request(self.browser_config.method, url, **request_kwargs) as response:
                    raw_bytes = await response.read()
                    content = memoryview(raw_bytes)

                    if not (200 <= response.status < 300):
                        raise HTTPStatusError(
                            response.status,
                            f"Unexpected status code for {url}"
                        )

                    response_headers = dict(response.headers)
                    content_type = response.content_type or 'text/html'
                    content_type = content_type.split(';')[0].strip().lower()
                    content_disposition = response_headers.get('Content-Disposition', '')

                    downloaded_files = None
                    html = ""

                    if self._is_file_download(content_type, content_disposition):
                        # Save file to disk
                        downloads_path = self.browser_config.downloads_path or os.path.join(
                            os.path.expanduser("~"), ".crawl4ai", "downloads"
                        )
                        os.makedirs(downloads_path, exist_ok=True)

                        filename = self._extract_filename(content_disposition, url, content_type)
                        filepath = os.path.join(downloads_path, filename)

                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(raw_bytes)

                        downloaded_files = [filepath]

                        # For text-based files, also decode into html (backward compatible)
                        if self._is_text_content(content_type):
                            encoding = response.charset
                            if not encoding:
                                detection_result = await asyncio.to_thread(chardet.detect, raw_bytes)
                                encoding = detection_result['encoding'] or 'utf-8'
                            html = raw_bytes.decode(encoding, errors='replace')
                    else:
                        # Standard HTML response — existing behavior
                        encoding = response.charset
                        if not encoding:
                            detection_result = await asyncio.to_thread(chardet.detect, content.tobytes())
                            encoding = detection_result['encoding'] or 'utf-8'
                        html = content.tobytes().decode(encoding, errors='replace')

                    result = AsyncCrawlResponse(
                        html=html,
                        response_headers=response_headers,
                        status_code=response.status,
                        redirected_url=str(response.url),
                        downloaded_files=downloaded_files,
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