async def test_config_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, bypass_api: AsyncMock
) -> None:
    """Test we create the entry successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username"
    assert result["data"] == {
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }
    assert result["result"].unique_id == "123e4567-e89b-12d3-a456-426614174000"
    assert len(mock_setup_entry.mock_calls) == 1