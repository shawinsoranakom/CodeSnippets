async def _handle_request(
        self, request: web.Request, token: str, path: str
    ) -> web.Response | web.StreamResponse:
        """Ingress route for request."""
        url = self._create_url(token, path)
        source_header = _init_header(request, token)

        async with self._websession.request(
            request.method,
            url,
            headers=source_header,
            params=request.query,
            allow_redirects=False,
            data=request.content if request.method != "GET" else None,
            timeout=DISABLED_TIMEOUT,
            skip_auto_headers={hdrs.CONTENT_TYPE},
        ) as result:
            headers = _response_header(result)

            # Avoid parsing content_type in simple cases for better performance
            if maybe_content_type := result.headers.get(hdrs.CONTENT_TYPE):
                content_type: str = (maybe_content_type.partition(";"))[0].strip()
            else:
                # default value according to RFC 2616
                content_type = "application/octet-stream"

            # Empty body responses (304, 204, HEAD, etc.) should not be streamed,
            # otherwise aiohttp < 3.9.0 may generate an invalid "0\r\n\r\n" chunk
            # This also avoids setting content_type for empty responses.
            if must_be_empty_body(request.method, result.status):
                # If upstream contains content-type, preserve it (e.g. for HEAD requests)
                # Note: This still is omitting content-length. We can't simply forward
                # the upstream length since the proxy might change the body length
                # (e.g. due to compression).
                if maybe_content_type:
                    headers[hdrs.CONTENT_TYPE] = content_type
                return web.Response(
                    headers=headers,
                    status=result.status,
                )

            # Simple request
            content_length_int = 0
            content_length = result.headers.get(hdrs.CONTENT_LENGTH, UNDEFINED)
            if (
                content_length is not UNDEFINED
                and (content_length_int := int(content_length))
                <= MAX_SIMPLE_RESPONSE_SIZE
            ):
                body = await result.read()
                simple_response = web.Response(
                    headers=headers,
                    status=result.status,
                    content_type=content_type,
                    body=body,
                    zlib_executor_size=32768,
                )
                if content_length_int > MIN_COMPRESSED_SIZE and should_compress(
                    content_type
                ):
                    simple_response.enable_compression()
                return simple_response

            # Stream response
            response = web.StreamResponse(status=result.status, headers=headers)
            response.content_type = content_type

            try:
                if should_compress(content_type):
                    response.enable_compression()
                await response.prepare(request)
                # In testing iter_chunked, iter_any, and iter_chunks:
                # iter_chunks was the best performing option since
                # it does not have to do as much re-assembly
                async for data, _ in result.content.iter_chunks():
                    await response.write(data)

            except (
                aiohttp.ClientError,
                aiohttp.ClientPayloadError,
                ConnectionResetError,
                ConnectionError,
            ) as err:
                _LOGGER.debug("Stream error %s / %s: %s", token, path, err)

            return response