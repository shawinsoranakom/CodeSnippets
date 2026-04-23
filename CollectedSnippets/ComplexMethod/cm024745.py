async def test_user_selection_incorrect_pin(
    hass: HomeAssistant,
    mock_automower_client: Mock,
) -> None:
    """Test we can select a device."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Try non numeric pin
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
            CONF_PIN: "ABCD",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_pin"}

    # Try wrong PIN
    mock_automower_client.connect.return_value = ResponseResult.INVALID_PIN
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
            CONF_PIN: "1234",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    mock_automower_client.connect.return_value = ResponseResult.OK

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
            CONF_PIN: "1234",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert result["data"] == {
        CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
        CONF_CLIENT_ID: 1197489078,
        CONF_PIN: "1234",
    }