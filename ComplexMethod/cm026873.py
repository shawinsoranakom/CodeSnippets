async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    user = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    host = urlparse(data[CONF_HOST])
    tls_version = data.get(CONF_TLS_VER)

    if host.scheme == SCHEME_HTTP:
        https = False
        port = host.port or HTTP_PORT
        session = aiohttp_client.async_create_clientsession(
            hass, verify_ssl=False, cookie_jar=CookieJar(unsafe=True)
        )
    elif host.scheme == SCHEME_HTTPS:
        https = True
        port = host.port or HTTPS_PORT
        session = aiohttp_client.async_get_clientsession(hass)
    else:
        _LOGGER.error("The ISY/IoX host value in configuration is invalid")
        raise InvalidHost

    # Connect to ISY controller.
    isy_conn = Connection(
        host.hostname,
        port,
        user,
        password,
        use_https=https,
        tls_ver=tls_version,
        webroot=host.path,
        websession=session,
    )

    try:
        async with asyncio.timeout(30):
            isy_conf_xml = await isy_conn.test_connection()
    except ISYInvalidAuthError as error:
        raise InvalidAuth from error
    except ISYConnectionError as error:
        raise CannotConnect from error

    try:
        isy_conf = Configuration(xml=isy_conf_xml)
    except ISYResponseParseError as error:
        raise CannotConnect from error
    if not isy_conf or ISY_CONF_NAME not in isy_conf or not isy_conf[ISY_CONF_NAME]:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {
        "title": f"{isy_conf[ISY_CONF_NAME]} ({host.hostname})",
        ISY_CONF_UUID: isy_conf[ISY_CONF_UUID],
    }