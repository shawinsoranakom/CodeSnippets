async def test_failed_yaml_import(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    mock_london_underground_client,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a YAML sensor is imported and becomes an operational config entry."""
    # Set up via YAML which will trigger import and set up the config entry
    mock_london_underground_client.update.side_effect = asyncio.TimeoutError
    VALID_CONFIG = {
        "sensor": {"platform": "london_underground", CONF_LINE: ["Metropolitan"]}
    }
    assert await async_setup_component(hass, "sensor", VALID_CONFIG)
    await hass.async_block_till_done()

    # Verify the config entry was not created
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 0

    # verify no flows still in progress
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 0

    assert any(
        "Unexpected error trying to connect before importing config" in record.message
        for record in caplog.records
    )
    # Confirm that the import did not happen
    assert not any(
        "Importing London Underground config from configuration.yaml" in record.message
        for record in caplog.records
    )

    assert not any(
        "migrated to a config entry and can be safely removed" in record.message
        for record in caplog.records
    )

    # Verify a warning was issued about YAML not being imported
    assert issue_registry.async_get_issue(
        DOMAIN, "deprecated_yaml_import_issue_cannot_connect"
    )