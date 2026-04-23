async def test_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    entry: MockConfigEntry,
    entity_id: str,
    request_methods: list[str],
    return_values: list[ModStatusOutput | ModStatusRelays],
) -> None:
    """Test the availability of cover entity."""
    await init_integration(hass, entry)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE

    # no response from device -> unavailable
    with patch.multiple(
        MockDeviceConnection,
        **{
            request_method: AsyncMock(return_value=None)
            for request_method in request_methods
        },
    ):
        freezer.tick(SCAN_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    with patch.multiple(
        MockDeviceConnection,
        **{
            request_method: AsyncMock(return_value=return_value)
            for request_method, return_value in zip(
                request_methods, return_values, strict=True
            )
        },
    ):
        freezer.tick(SCAN_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE