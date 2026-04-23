async def websocket_detect_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Detect core config."""
    session = async_get_clientsession(hass)
    location_info = await location_util.async_detect_location_info(session)

    info: dict[str, Any] = {}

    if location_info is None:
        connection.send_result(msg["id"], info)
        return

    # We don't want any integrations to use the name of the unit system
    # so we are using the private attribute here
    if location_info.use_metric:
        info["unit_system"] = unit_system._CONF_UNIT_SYSTEM_METRIC  # noqa: SLF001
    else:
        info["unit_system"] = unit_system._CONF_UNIT_SYSTEM_US_CUSTOMARY  # noqa: SLF001

    if location_info.latitude:
        info["latitude"] = location_info.latitude

    if location_info.longitude:
        info["longitude"] = location_info.longitude

    if location_info.time_zone:
        info["time_zone"] = location_info.time_zone

    if location_info.currency:
        info["currency"] = location_info.currency

    if location_info.country_code:
        info["country"] = location_info.country_code

    connection.send_result(msg["id"], info)