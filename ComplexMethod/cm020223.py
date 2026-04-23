async def test_unload_entry(hass: HomeAssistant) -> None:
    """Test being able to unload an entry."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host})
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert len(hass.config_entries.async_entries(dynalite.DOMAIN)) == 1
    with patch.object(
        hass.config_entries, "async_forward_entry_unload", return_value=True
    ) as mock_unload:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert mock_unload.call_count == len(dynalite.PLATFORMS)
        expected_calls = [call(entry, platform) for platform in dynalite.PLATFORMS]
        for cur_call in mock_unload.mock_calls:
            assert cur_call in expected_calls