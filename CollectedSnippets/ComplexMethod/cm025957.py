async def _handle(self, request: web.Request, path: str) -> web.StreamResponse:
        """Return a client request with proxy origin for Hass.io supervisor.

        Use cases:
        - Onboarding allows restoring backups
        - Load Supervisor panel and add-on logo unauthenticated
        - User upload/restore backups
        """
        # No bullshit
        if path != unquote(path):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        hass = request.app[KEY_HASS]
        is_admin = request[KEY_AUTHENTICATED] and request[KEY_HASS_USER].is_admin
        authorized = is_admin

        if is_admin:
            allowed_paths = PATHS_ADMIN

        elif not async_is_onboarded(hass):
            allowed_paths = PATHS_NOT_ONBOARDED

            # During onboarding we need the user to manage backups
            authorized = True

        else:
            # Either unauthenticated or not an admin
            allowed_paths = PATHS_NO_AUTH

        no_auth_path = PATHS_NO_AUTH.match(path)
        headers = {
            X_HASS_SOURCE: "core.http",
        }

        if no_auth_path:
            if request.method != "GET":
                return web.Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

        else:
            if not allowed_paths.match(path):
                return web.Response(status=HTTPStatus.UNAUTHORIZED)

            if authorized:
                headers[AUTHORIZATION] = (
                    f"Bearer {os.environ.get('SUPERVISOR_TOKEN', '')}"
                )

            if request.method == "POST":
                headers[CONTENT_TYPE] = request.content_type
                # _stored_content_type is only computed once `content_type` is accessed
                if path == "backups/new/upload":
                    # We need to reuse the full content type that includes the boundary
                    if TYPE_CHECKING:
                        assert isinstance(request._stored_content_type, str)  # noqa: SLF001
                    headers[CONTENT_TYPE] = request._stored_content_type  # noqa: SLF001

            # forward range headers for logs
            if PATHS_LOGS.match(path) and request.headers.get(RANGE):
                headers[RANGE] = request.headers[RANGE]

        try:
            client = await self._websession.request(
                method=request.method,
                url=f"http://{self._host}/{quote(path)}",
                params=request.query,
                data=request.content if request.method != "GET" else None,
                headers=headers,
                timeout=_get_timeout(path),
            )

            # Stream response
            response = web.StreamResponse(
                status=client.status, headers=_response_header(client)
            )
            response.content_type = client.content_type

            if should_compress(response.content_type, path):
                response.enable_compression()
            await response.prepare(request)
            # In testing iter_chunked, iter_any, and iter_chunks:
            # iter_chunks was the best performing option since
            # it does not have to do as much re-assembly
            async for data, _ in client.content.iter_chunks():
                await response.write(data)

        except aiohttp.ClientError as err:
            _LOGGER.error("Client error on api %s request %s", path, err)
            raise HTTPBadGateway from err
        except TimeoutError as err:
            _LOGGER.error("Client timeout error on API request %s", path)
            raise HTTPBadGateway from err
        return response