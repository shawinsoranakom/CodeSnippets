async def test_remove_entry_cancels_reauth(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Tests that removing a config entry also aborts existing reauth flows."""
    entry = MockConfigEntry(title="test_title", domain="test")

    mock_setup_entry = AsyncMock(side_effect=ConfigEntryAuthFailed())
    mock_integration(hass, MockModule("test", async_setup_entry=mock_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    entry.add_to_hass(hass)
    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress_by_handler("test")
    assert len(flows) == 1
    assert flows[0]["context"]["entry_id"] == entry.entry_id
    assert flows[0]["context"]["source"] == config_entries.SOURCE_REAUTH
    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR

    issue_id = f"config_entry_reauth_test_{entry.entry_id}"
    assert issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)

    await manager.async_remove(entry.entry_id)

    flows = hass.config_entries.flow.async_progress_by_handler("test")
    assert len(flows) == 0
    assert not issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)