async def fetch_redirect_uris(hass: HomeAssistant, url: str) -> list[str]:
    """Find link tag with redirect_uri values.

    IndieAuth 4.2.2

    The client SHOULD publish one or more <link> tags or Link HTTP headers with
    a rel attribute of redirect_uri at the client_id URL.

    We limit to the first 10kB of the page.

    We do not implement extracting redirect uris from headers.
    """
    parser = LinkTagParser("redirect_uri")
    chunks = 0
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp,
        ):
            async for data in resp.content.iter_chunked(1024):
                parser.feed(data.decode())
                chunks += 1

                if chunks == 10:
                    break

    except TimeoutError:
        _LOGGER.error("Timeout while looking up redirect_uri %s", url)
    except aiohttp.client_exceptions.ClientSSLError:
        _LOGGER.error("SSL error while looking up redirect_uri %s", url)
    except aiohttp.client_exceptions.ClientOSError as ex:
        _LOGGER.error("OS error while looking up redirect_uri %s: %s", url, ex.strerror)
    except aiohttp.client_exceptions.ClientConnectionError:
        _LOGGER.error(
            "Low level connection error while looking up redirect_uri %s", url
        )
    except aiohttp.client_exceptions.ClientError:
        _LOGGER.error("Unknown error while looking up redirect_uri %s", url)

    # Authorization endpoints verifying that a redirect_uri is allowed for use
    # by a client MUST look for an exact match of the given redirect_uri in the
    # request against the list of redirect_uris discovered after resolving any
    # relative URLs.
    return [urljoin(url, found) for found in parser.found]