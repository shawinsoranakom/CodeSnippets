async def test_http_error(hass: HomeAssistant) -> None:
    """Test http error."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch("lacrosse_view.LaCrosse.get_devices", side_effect=HTTPError),
    ):
        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.SETUP_RETRY

    config_entry_2 = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    config_entry_2.add_to_hass(hass)

    # Start over, let get_devices succeed but get_sensor_status fail
    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch("lacrosse_view.LaCrosse.get_devices", return_value=[TEST_SENSOR]),
        patch("lacrosse_view.LaCrosse.get_sensor_status", side_effect=HTTPError),
    ):
        assert not await hass.config_entries.async_setup(config_entry_2.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries
    assert len(entries) == 2
    assert entries[1].state is ConfigEntryState.SETUP_RETRY