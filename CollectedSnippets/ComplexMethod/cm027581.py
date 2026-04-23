async def _ssrf_redirect_middleware(
    request: aiohttp.ClientRequest,
    handler: aiohttp.ClientHandlerType,
) -> aiohttp.ClientResponse:
    """Block redirects from non-loopback origins to loopback targets."""
    resp = await handler(request)

    # Return early if not a redirect or already loopback to allow loopback origins
    connector = request.session.connector
    if not (300 <= resp.status < 400) or await _async_is_blocked_host(
        request.url.host, connector
    ):
        return resp

    location = resp.headers.get(hdrs.LOCATION, "")
    if not location:
        return resp

    redirect_url = URL(location)
    if not redirect_url.is_absolute():
        # Relative redirects stay on the same host - always safe
        return resp

    # Only schemes that aiohttp can open a network connection for need
    # SSRF protection. Custom app URI schemes (e.g. weconnect://) are inert
    # from a networking perspective and must not be blocked.
    if connector and redirect_url.scheme not in connector.allowed_protocol_schema_set:
        return resp

    host = redirect_url.host
    if await _async_is_blocked_host(host, connector):
        resp.close()
        raise SSRFRedirectError(
            f"Redirect from {request.url.host} to a blocked address"
            f" is not allowed: {host}"
        )

    return resp