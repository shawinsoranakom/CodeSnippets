async def async_send_to_emoncms(
    hass: HomeAssistant,
    emoncms_client: EmoncmsClient,
    whitelist: list[str],
    node: str | int,
    _: datetime,
) -> None:
    """Send data to Emoncms."""
    payload_dict = {}

    for entity_id in whitelist:
        state = hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, "", STATE_UNAVAILABLE):
            continue
        try:
            payload_dict[entity_id] = state_helper.state_as_number(state)
        except ValueError:
            continue

    if payload_dict:
        try:
            await emoncms_client.async_input_post(data=payload_dict, node=node)
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Network error when sending data to Emoncms: %s", err)
        except ValueError as err:
            _LOGGER.warning("Value error when preparing data for Emoncms: %s", err)
        else:
            _LOGGER.debug("Sent data to Emoncms: %s", payload_dict)