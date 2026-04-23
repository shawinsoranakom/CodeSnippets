async def auth_middleware(
        request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]
    ) -> StreamResponse:
        """Authenticate as middleware."""
        authenticated = False

        if is_supervisor_unix_socket_request(request):
            authenticated = await async_authenticate_supervisor_unix_socket(request)
            auth_type = "supervisor unix socket"

        elif hdrs.AUTHORIZATION in request.headers and async_validate_auth_header(
            request
        ):
            authenticated = True
            auth_type = "bearer token"

        # We first start with a string check to avoid parsing query params
        # for every request.
        elif (
            request.method in ["GET", "HEAD"]
            and SIGN_QUERY_PARAM in request.query_string
            and async_validate_signed_request(request)
        ):
            authenticated = True
            auth_type = "signed request"

        if authenticated and _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Authenticated %s for %s using %s",
                request.remote or "unknown remote",
                request.path,
                auth_type,
            )

        request[KEY_AUTHENTICATED] = authenticated
        return await handler(request)