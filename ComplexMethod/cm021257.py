async def test_failed_token(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test if a reauth flow occurs when token refresh fails."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    sensor = TEST_SENSOR.model_copy()
    status = sensor.data
    sensor.data = None

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True) as login,
        patch(
            "lacrosse_view.LaCrosse.get_devices",
            return_value=[sensor],
        ),
        patch("lacrosse_view.LaCrosse.get_sensor_status", return_value=status),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        login.assert_called_once()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED

    with patch("lacrosse_view.LaCrosse.login", side_effect=LoginError("Test")):
        freezer.tick(timedelta(hours=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"