async def _update_freedns(hass, session, url, auth_token):
    """Update FreeDNS."""
    params = None

    if url is None:
        url = UPDATE_URL

    if auth_token is not None:
        params = {}
        params[auth_token] = ""

    try:
        async with asyncio.timeout(TIMEOUT):
            resp = await session.get(url, params=params)
            body = await resp.text()

            if "has not changed" in body:
                # IP has not changed.
                _LOGGER.debug("FreeDNS update skipped: IP has not changed")
                return True

            if "ERROR" not in body:
                _LOGGER.debug("Updating FreeDNS was successful: %s", body)
                return True

            if "Invalid update URL" in body:
                _LOGGER.error("FreeDNS update token is invalid")
            else:
                _LOGGER.warning("Updating FreeDNS failed: %s", body)

    except aiohttp.ClientError:
        _LOGGER.warning("Can't connect to FreeDNS API")

    except TimeoutError:
        _LOGGER.warning("Timeout from FreeDNS API at %s", url)

    return False