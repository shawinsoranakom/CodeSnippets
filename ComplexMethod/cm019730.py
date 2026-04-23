async def test_basic_setup(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_client: MagicMock
) -> None:
    """Test we get and complete the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "1234567890",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["version"] == 2
    assert result["title"] == "firstnamelastname"
    assert result["result"].unique_id == "firstnamelastname"
    assert result["data"] == {
        CONF_API_KEY: "1234567890",
    }

    assert len(mock_setup_entry.mock_calls) == 1