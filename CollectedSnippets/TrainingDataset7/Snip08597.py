async def send_response(self, response, send):
        """Encode and send a response out over ASGI."""
        # Collect cookies into headers. Have to preserve header case as there
        # are some non-RFC compliant clients that require e.g. Content-Type.
        response_headers = []
        for header, value in response.items():
            if isinstance(header, str):
                header = header.encode("ascii")
            if isinstance(value, str):
                value = value.encode("latin1")
            response_headers.append((bytes(header), bytes(value)))
        for c in response.cookies.values():
            response_headers.append((b"Set-Cookie", c.OutputString().encode("ascii")))
        # Initial response message.
        await send(
            {
                "type": "http.response.start",
                "status": response.status_code,
                "headers": response_headers,
            }
        )
        # Streaming responses need to be pinned to their iterator.
        if response.streaming:
            # - Consume via `__aiter__` and not `streaming_content` directly,
            #   to allow mapping of a sync iterator.
            # - Use aclosing() when consuming aiter. See
            #   https://github.com/python/cpython/commit/6e8dcdaaa49d4313bf9fab9f9923ca5828fbb10e
            async with aclosing(aiter(response)) as content:
                async for part in content:
                    for chunk, _ in self.chunk_bytes(part):
                        await send(
                            {
                                "type": "http.response.body",
                                "body": chunk,
                                # Ignore "more" as there may be more parts;
                                # instead, use an empty final closing message
                                # with False.
                                "more_body": True,
                            }
                        )
            # Final closing message.
            await send({"type": "http.response.body"})
        # Other responses just need chunking.
        else:
            # Yield chunks of response.
            for chunk, last in self.chunk_bytes(response.content):
                await send(
                    {
                        "type": "http.response.body",
                        "body": chunk,
                        "more_body": not last,
                    }
                )