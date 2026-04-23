async def validate_input(data: dict[str, Any]) -> str:
    """Validate the user input allows us to connect.

    Data has the keys from SSDP values as well as user input.

    Returns the installation id upon success.
    """
    _LOGGER.debug("Validating input: %s", async_redact_data(data, TO_REDACT))
    hub: VictronVenusHub | None = None
    try:
        hub = VictronVenusHub(
            host=data[CONF_HOST],
            port=int(data[CONF_PORT]),
            username=data.get(CONF_USERNAME) or None,
            password=data.get(CONF_PASSWORD) or None,
            use_ssl=data.get(CONF_SSL, False),
            installation_id=data.get(CONF_INSTALLATION_ID) or None,
            serial=data.get(CONF_SERIAL) or None,
        )

        await hub.connect()
        if hub.installation_id is None:
            raise CannotConnectError("Victron hub did not provide an installation_id")

        return hub.installation_id
    finally:
        if hub is not None:
            try:
                await hub.disconnect()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Ignoring disconnect error during config validation")