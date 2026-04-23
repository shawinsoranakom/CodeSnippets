async def test_deprecated_platform_config(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    cloud: MagicMock,
) -> None:
    """Test cloud provider uses the preferences."""
    assert await async_setup_component(
        hass, TTS_DOMAIN, {TTS_DOMAIN: {"platform": DOMAIN}}
    )
    await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(DOMAIN, "deprecated_tts_platform_config")
    assert issue is not None
    assert issue.breaks_in_ha_version == "2024.9.0"
    assert issue.is_fixable is False
    assert issue.is_persistent is False
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.translation_key == "deprecated_tts_platform_config"