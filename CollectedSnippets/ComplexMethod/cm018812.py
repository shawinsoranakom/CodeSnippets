async def test_service_pin_creates_repair_issue(
    hass: HomeAssistant,
    mock_blink_api: MagicMock,
    mock_blink_auth_api: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that the send PIN service creates a repair issue."""

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issue_registry = ir.async_get(hass)

    # Initially no issues
    assert len(issue_registry.issues) == 0

    # Call the service (should fail but create repair issue)
    with pytest.raises(
        HomeAssistantError, match="The service blink.send_pin has been removed"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_PIN,
            {ATTR_CONFIG_ENTRY_ID: [mock_config_entry.entry_id], CONF_PIN: PIN},
            blocking=True,
        )

    # Verify repair issue was created
    issues = issue_registry.issues
    assert len(issues) == 1
    issue = next(iter(issues.values()))
    assert issue.issue_id == "service_send_pin_deprecation"
    assert issue.domain == DOMAIN
    assert issue.severity == ir.IssueSeverity.ERROR
    assert not issue.is_fixable

    # Call service again - should not create duplicate issue
    with pytest.raises(
        HomeAssistantError, match="The service blink.send_pin has been removed"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_PIN,
            {ATTR_CONFIG_ENTRY_ID: [mock_config_entry.entry_id], CONF_PIN: PIN},
            blocking=True,
        )

    # Still only one issue
    assert len(issue_registry.issues) == 1