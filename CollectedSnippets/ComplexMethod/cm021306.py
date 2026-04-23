async def test_full_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_client: AsyncMock
) -> None:
    """Test user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "locations"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PASSWORD: PASSWORD,
        CONF_USERNAME: USERNAME,
        CONF_USERCODES: {LOCATION_ID: "7890"},
    }
    assert result["title"] == "Total Connect"
    assert result["options"] == {}
    assert result["result"].unique_id == USERNAME