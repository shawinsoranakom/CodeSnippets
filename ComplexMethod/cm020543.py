async def test_submitting_empty_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_analytics_client: AsyncMock,
    user_input: dict[str, Any],
) -> None:
    """Test we can't submit an empty form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_integrations_selected"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TRACKED_APPS: ["core_samba"],
            CONF_TRACKED_INTEGRATIONS: ["youtube"],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home Assistant Analytics Insights"
    assert result["data"] == {}
    assert result["options"] == {
        CONF_TRACKED_APPS: ["core_samba"],
        CONF_TRACKED_INTEGRATIONS: ["youtube"],
        CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
    }
    assert len(mock_setup_entry.mock_calls) == 1