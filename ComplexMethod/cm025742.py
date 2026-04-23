async def validate_input(data: dict[str, str], mac: str | None) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    userid = data.get(CONF_USERNAME)
    password = data.get(CONF_PASSWORD)

    prefix = data[CONF_PREFIX]
    url = _make_url_from_data(data)
    requires_password = url.startswith(("elks://", "elksv1_2"))

    if requires_password and (not userid or not password):
        raise InvalidAuth

    elk = Elk(
        {"url": url, "userid": userid, "password": password, "element_list": ["panel"]}
    )
    elk.connect()

    try:
        await ElkSyncWaiter(elk, LOGIN_TIMEOUT, VALIDATE_TIMEOUT).async_wait()
    except LoginFailed as exc:
        raise InvalidAuth from exc
    finally:
        elk.disconnect()

    short_mac = _short_mac(mac) if mac else None
    if prefix and prefix != short_mac:
        device_name = prefix
    elif mac:
        device_name = f"ElkM1 {short_mac}"
    else:
        device_name = "ElkM1"
    return {"title": device_name, CONF_HOST: url, CONF_PREFIX: slugify(prefix)}