async def test_unload_entry_removes_repair_issue(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """Test that unloading the last config entry removes the repair issue."""
    first_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Volvo On Call",
        data={},
    )
    first_config_entry.add_to_hass(hass)
    second_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Volvo On Call second",
        data={},
    )
    second_config_entry.add_to_hass(hass)

    # Setup entry
    assert await hass.config_entries.async_setup(first_config_entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(DOMAIN)) == 2

    # Check that the repair issue was created
    issue = issue_registry.async_get_issue(DOMAIN, "volvooncall_deprecated")
    assert issue is not None

    # Unload entry (this is the only entry, so issue should be removed)
    assert await hass.config_entries.async_remove(first_config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    # Check that the repair issue still exists because there's another entry
    issue = issue_registry.async_get_issue(DOMAIN, "volvooncall_deprecated")
    assert issue is not None

    # Unload entry (this is the only entry, so issue should be removed)
    assert await hass.config_entries.async_remove(second_config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Check that the repair issue was removed
    issue = issue_registry.async_get_issue(DOMAIN, "volvooncall_deprecated")
    assert issue is None