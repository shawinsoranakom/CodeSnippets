async def test_full_cloud_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_geniushub_client: AsyncMock,
) -> None:
    """Test full cloud flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "cloud_api"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_api"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "abcdef",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Genius hub"
    assert result["data"] == {
        CONF_TOKEN: "abcdef",
    }