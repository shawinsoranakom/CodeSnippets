async def test_setup_with_recommended_version_repair(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    rest_client: AsyncMock,
    config: ConfigType,
) -> None:
    """Test setup integration entry fails."""
    rest_client.validate_server_version.return_value = AwesomeVersion("1.9.5")
    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Verify the issue is created
    issue = issue_registry.async_get_issue(DOMAIN, "recommended_version")
    assert issue
    assert issue.is_fixable is False
    assert issue.is_persistent is False
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.issue_id == "recommended_version"
    assert issue.translation_key == "recommended_version"
    assert issue.translation_placeholders == {
        "recommended_version": RECOMMENDED_VERSION,
        "current_version": "1.9.5",
    }