async def test_duplicate_config_entries(
    hass: HomeAssistant, oauth, setup_platform
) -> None:
    """Verify that config entries must be for unique projects."""
    await setup_platform()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "cloud_project"

    result = await oauth.async_configure(result, {"cloud_project_id": CLOUD_PROJECT_ID})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "device_project"

    result = await oauth.async_configure(result, {"project_id": PROJECT_ID})
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "already_configured"