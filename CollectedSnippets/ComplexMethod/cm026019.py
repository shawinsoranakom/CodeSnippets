async def determine_api_version(
    hass: HomeAssistant, entry: dict[str, Any]
) -> Literal[5, 6]:
    """Determine the API version of the Pi-hole instance without requiring authentication.

    Neither API v5 or v6 provides an endpoint to check the version without authentication.
    Version 6 provides other enddpoints that do not require authentication, so we can use those to determine the version
    version 5 returns an empty list in response to unauthenticated requests.
    Because we are using endpoints that are not designed for this purpose, we should log liberally to help with debugging.
    """

    holeV6 = api_by_version(hass, entry, 6, password="wrong_password")
    try:
        await holeV6.authenticate()
    except HoleConnectionError as err:
        _LOGGER.error(
            "Unexpected error connecting to Pi-hole v6 API at %s: %s. Trying version 5 API",
            holeV6.base_url,
            err,
        )
    # Ideally python-hole would raise a specific exception for authentication failures
    except HoleError as ex_v6:
        if str(ex_v6) == "Authentication failed: Invalid password":
            _LOGGER.debug(
                "Success connecting to Pi-hole at %s without auth, API version is : %s",
                holeV6.base_url,
                6,
            )
            return 6
        _LOGGER.debug(
            "Connection to %s failed: %s, trying API version 5", holeV6.base_url, ex_v6
        )
    else:
        # It seems that occasionally the auth can succeed unexpectedly when there is a valid session
        _LOGGER.warning(
            "Authenticated with %s through v6 API, but succeeded with an incorrect password. This is a known bug",
            holeV6.base_url,
        )
        return 6
    holeV5 = api_by_version(hass, entry, 5, password="wrong_token")
    try:
        await holeV5.get_data()

    except HoleConnectionError as err:
        _LOGGER.error(
            "Failed to connect to Pi-hole v5 API at %s: %s", holeV5.base_url, err
        )
    else:
        # V5 API returns [] to unauthenticated requests
        if not holeV5.data:
            _LOGGER.debug(
                "Response '[]' from API without auth, pihole API version 5 probably detected at %s",
                holeV5.base_url,
            )
            return 5
        _LOGGER.debug(
            "Unexpected response from Pi-hole API at %s: %s",
            holeV5.base_url,
            str(holeV5.data),
        )
    _LOGGER.debug(
        "Could not determine pi-hole API version at: %s",
        holeV6.base_url,
    )
    raise HoleError("Could not determine Pi-hole API version")