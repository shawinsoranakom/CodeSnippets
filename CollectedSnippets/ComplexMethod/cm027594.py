async def handle(request: web.Request) -> web.StreamResponse:
        """Handle incoming request."""
        if hass.is_stopping:
            return web.Response(status=HTTPStatus.SERVICE_UNAVAILABLE)

        authenticated = request.get(KEY_AUTHENTICATED, False)

        if view.requires_auth and not authenticated:
            # Import here to avoid circular dependency with network.py
            from .network import NoURLAvailableError, get_url  # noqa: PLC0415

            try:
                url_prefix = get_url(hass, require_current_request=True)
            except NoURLAvailableError:
                # Omit header to avoid leaking configured URLs
                raise HTTPUnauthorized from None
            raise HTTPUnauthorized(
                # Include resource metadata endpoint for RFC9728
                headers={
                    "WWW-Authenticate": (
                        f'Bearer resource_metadata="{url_prefix}'
                        '/.well-known/oauth-protected-resource"'
                    )
                }
            )

        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Serving %s to %s (auth: %s)",
                request.path,
                request.remote,
                authenticated,
            )

        try:
            if is_coroutinefunction:
                result = await handler(request, **request.match_info)
            else:
                result = handler(request, **request.match_info)
        except vol.Invalid as err:
            raise HTTPBadRequest from err
        except exceptions.ServiceNotFound as err:
            raise HTTPInternalServerError from err
        except exceptions.Unauthorized as err:
            raise HTTPUnauthorized from err

        if isinstance(result, web.StreamResponse):
            # The method handler returned a ready-made Response, how nice of it
            return result

        status_code = HTTPStatus.OK
        if isinstance(result, tuple):
            result, status_code = result

        if isinstance(result, bytes):
            return web.Response(body=result, status=status_code)

        if isinstance(result, str):
            return web.Response(text=result, status=status_code)

        if result is None:
            return web.Response(body=b"", status=status_code)

        raise TypeError(
            f"Result should be None, string, bytes or StreamResponse. Got: {result}"
        )