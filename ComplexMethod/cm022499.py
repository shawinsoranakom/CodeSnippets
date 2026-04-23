async def test_update_errors(
    hass: HomeAssistant,
    mock_airgradient_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test update entity errors."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("update.airgradient_firmware")
    assert state.state == STATE_ON
    mock_airgradient_client.get_latest_firmware_version.side_effect = (
        AirGradientConnectionError("Boom")
    )

    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("update.airgradient_firmware")
    assert state.state == STATE_UNAVAILABLE

    assert "Unable to connect to AirGradient server to check for updates" in caplog.text

    caplog.clear()

    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("update.airgradient_firmware")
    assert state.state == STATE_UNAVAILABLE

    assert (
        "Unable to connect to AirGradient server to check for updates"
        not in caplog.text
    )

    mock_airgradient_client.get_latest_firmware_version.side_effect = None

    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("update.airgradient_firmware")
    assert state.state == STATE_ON
    mock_airgradient_client.get_latest_firmware_version.side_effect = (
        AirGradientConnectionError("Boom")
    )

    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("update.airgradient_firmware")
    assert state.state == STATE_UNAVAILABLE

    assert "Unable to connect to AirGradient server to check for updates" in caplog.text