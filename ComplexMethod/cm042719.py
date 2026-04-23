async def download_request(self, request: Request) -> Response:
        self._warn_unsupported_meta(request.meta)

        timeout: float = request.meta.get(
            "download_timeout", self._DEFAULT_CONNECT_TIMEOUT
        )
        start_time = time.monotonic()
        try:
            async with self._get_httpx_response(request, timeout) as httpx_response:
                request.meta["download_latency"] = time.monotonic() - start_time
                return await self._read_response(httpx_response, request)
        except httpx.TimeoutException as e:
            raise DownloadTimeoutError(
                f"Getting {request.url} took longer than {timeout} seconds."
            ) from e
        except httpx.UnsupportedProtocol as e:
            raise UnsupportedURLSchemeError(str(e)) from e
        except httpx.ConnectError as e:
            error_message = str(e)
            if (
                "Name or service not known" in error_message
                or "getaddrinfo failed" in error_message
                or "nodename nor servname" in error_message
                or "Temporary failure in name resolution" in error_message
            ):
                raise CannotResolveHostError(error_message) from e
            raise DownloadConnectionRefusedError(str(e)) from e
        except httpx.NetworkError as e:
            raise DownloadFailedError(str(e)) from e
        except httpx.RemoteProtocolError as e:
            raise DownloadFailedError(str(e)) from e