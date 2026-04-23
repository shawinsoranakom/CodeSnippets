async def test_form_simple(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_config_api: AsyncMock
) -> None:
    """Test simple case (no MFA / no errors)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Monarch Money"
    assert result["data"] == {
        CONF_TOKEN: "mocked_token",
    }
    assert result["result"].unique_id == "222260252323873333"
    assert len(mock_setup_entry.mock_calls) == 1