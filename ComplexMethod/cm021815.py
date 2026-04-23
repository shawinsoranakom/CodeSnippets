async def test_async_setup_entry(hass: HomeAssistant) -> None:
    """Test a successful setup entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "mock", CONF_PORT: "mock"},
    )
    entry.add_to_hass(hass)

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"}, list_vars={"ups.status": "OL"}
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(hass.config_entries.async_entries(DOMAIN)) == 1
        assert entry.state is ConfigEntryState.LOADED

        state = hass.states.get("sensor.ups1_status_data")
        assert state is not None
        assert state.state != STATE_UNAVAILABLE
        assert state.state == "OL"

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.NOT_LOADED
        assert not hass.data.get(DOMAIN)