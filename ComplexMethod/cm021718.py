async def test_async_update_errors(
    hass: HomeAssistant,
    device: MagicMock,
    config_entry: MagicMock,
    client: MagicMock,
) -> None:
    """Test update with errors."""

    await init_integration(hass, config_entry)

    device.refresh.side_effect = aiosomecomfort.UnauthorizedError
    client.login.side_effect = aiosomecomfort.AuthError
    entity_id = f"climate.{device.name}"
    state = hass.states.get(entity_id)
    assert state.state == "off"

    # Due to server instability, only mark entity unavailable after RETRY update attempts
    for _ in range(RETRY):
        async_fire_time_changed(
            hass,
            utcnow() + SCAN_INTERVAL,
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == "off"

    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "unavailable"

    reset_mock(device)
    device.refresh.side_effect = None
    client.login.side_effect = None

    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "off"

    device.refresh.side_effect = aiosomecomfort.UnexpectedResponse
    client.login.side_effect = None
    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "off"

    device.refresh.side_effect = [aiosomecomfort.UnauthorizedError, None]
    client.login.side_effect = None
    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "off"

    device.refresh.side_effect = aiosomecomfort.SomeComfortError
    client.login.side_effect = aiosomecomfort.AuthError
    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "off"

    device.refresh.side_effect = ClientConnectionError

    # Due to server instability, only mark entity unavailable after RETRY update attempts
    for _ in range(RETRY):
        async_fire_time_changed(
            hass,
            utcnow() + SCAN_INTERVAL,
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == "off"

    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "unavailable"