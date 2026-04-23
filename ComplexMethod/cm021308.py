async def test_usercode_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_client: AsyncMock,
    mock_location: AsyncMock,
) -> None:
    """Test user step with usercode errors."""
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

    mock_location.set_usercode.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "locations"
    assert result["errors"] == {CONF_LOCATION: "usercode"}

    mock_location.set_usercode.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY