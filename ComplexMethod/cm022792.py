async def test_estimated_broadcast_interval(hass: HomeAssistant) -> None:
    """Test sensors get value when we receive a broadcast."""
    await async_mock_config_entry(hass)
    await async_inject_broadcast(hass, MAC_RPA_VALID_1)

    # With no fallback and no learned interval, we should use the global default

    state = hass.states.get(
        "sensor.private_ble_device_000000_estimated_broadcast_interval"
    )
    assert state
    assert state.state == "900"

    # Fallback interval trumps const default

    async_set_fallback_availability_interval(hass, MAC_RPA_VALID_1, 90)
    await async_inject_broadcast(hass, MAC_RPA_VALID_1.upper())

    state = hass.states.get(
        "sensor.private_ble_device_000000_estimated_broadcast_interval"
    )
    assert state
    assert state.state == "90.0"

    # Learned broadcast interval takes over from fallback interval

    for i in range(ADVERTISING_TIMES_NEEDED):
        await async_inject_broadcast(
            hass, MAC_RPA_VALID_1, mfr_data=bytes(i), broadcast_time=i * 10
        )

    state = hass.states.get(
        "sensor.private_ble_device_000000_estimated_broadcast_interval"
    )
    assert state
    assert state.state == "10.0"

    # MAC address changes, the broadcast interval is kept

    await async_inject_broadcast(hass, MAC_RPA_VALID_2.upper())

    state = hass.states.get(
        "sensor.private_ble_device_000000_estimated_broadcast_interval"
    )
    assert state
    assert state.state == "10.0"