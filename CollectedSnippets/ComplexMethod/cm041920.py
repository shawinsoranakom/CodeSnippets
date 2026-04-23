async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool]:
        """
        Interpret an asynchronous response.

        Args:
            result (aiohttp.ClientResponse): The response object.
            stream (bool): Whether the response is a stream.

        Returns:
            Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool]: A tuple containing the response content and a boolean indicating if it is a stream.
        """
        content_type = result.headers.get("Content-Type", "")
        if stream and (
            "text/event-stream" in content_type or "application/x-ndjson" in content_type or content_type == ""
        ):
            return (
                (
                    self._interpret_response_line(line, result.status, result.headers, stream=True)
                    async for line in result.content
                ),
                True,
            )
        else:
            try:
                response_content = await result.read()
            except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
                raise TimeoutError("Request timed out") from e
            except aiohttp.ClientError as exp:
                logger.warning(f"response: {result}, exp: {exp}")
                response_content = b""
            return (
                self._interpret_response_line(
                    response_content,  # let the caller decode the msg
                    result.status,
                    result.headers,
                    stream=False,
                ),
                False,
            )