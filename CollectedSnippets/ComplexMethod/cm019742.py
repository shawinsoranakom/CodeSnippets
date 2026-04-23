async def test_vehicle_sleep(
    hass: HomeAssistant,
    normal_config_entry: MockConfigEntry,
    mock_vehicle_data: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test coordinator refresh with an error."""

    TEST_INTERVAL = timedelta(seconds=120)

    with patch(
        "homeassistant.components.tesla_fleet.coordinator.VEHICLE_INTERVAL",
        TEST_INTERVAL,
    ):
        await setup_platform(hass, normal_config_entry)
        assert mock_vehicle_data.call_count == 1

        freezer.tick(VEHICLE_WAIT + TEST_INTERVAL)
        async_fire_time_changed(hass)
        # Let vehicle sleep, no updates for 15 minutes
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 2

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        # No polling, call_count should not increase
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 2

        freezer.tick(VEHICLE_WAIT)
        async_fire_time_changed(hass)
        # Vehicle didn't sleep, go back to normal
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 3

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        # Regular polling
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 4

        mock_vehicle_data.return_value = VEHICLE_DATA_ALT
        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        # Vehicle active
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 5

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        # Dont let sleep when active
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 6

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        # Dont let sleep when active
        await hass.async_block_till_done()
        assert mock_vehicle_data.call_count == 7