async def test_login_error(hass: HomeAssistant) -> None:
    """Test login error."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    with patch("lacrosse_view.LaCrosse.login", side_effect=LoginError("Test")):
        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"