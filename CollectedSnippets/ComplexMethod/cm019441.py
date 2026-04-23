async def test_update_unique_id(hass: HomeAssistant) -> None:
    """Test updating a config entry without a unique_id."""
    assert hass.state is CoreState.running

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT})
    entry.add_to_hass(hass)

    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]
    assert not entry.unique_id

    with patch(
        "homeassistant.components.cert_expiry.coordinator.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.unique_id == f"{HOST}:{PORT}"