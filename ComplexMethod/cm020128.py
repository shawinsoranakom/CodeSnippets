async def test_get_supervisor_info(hass: HomeAssistant) -> None:
    """Test get_supervisor_info returns a dict with backwards-compat keys."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    result = get_supervisor_info(hass)
    assert isinstance(result, dict)
    # Deprecated backwards-compat keys folded in from store/addons data
    assert "repositories" in result
    assert isinstance(result["repositories"], list)
    assert "addons" in result
    assert isinstance(result["addons"], list)
    assert all(isinstance(addon, dict) for addon in result["addons"])