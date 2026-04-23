async def test_authentication_correct_pin(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_motionmount: MagicMock,
) -> None:
    """Test that authentication is requested when needed."""
    type(mock_motionmount).name = PropertyMock(return_value=ZEROCONF_NAME)
    type(mock_motionmount).mac = PropertyMock(return_value=MAC)
    type(mock_motionmount).is_authenticated = PropertyMock(return_value=False)
    type(mock_motionmount).can_authenticate = PropertyMock(return_value=True)

    user_input = MOCK_USER_INPUT.copy()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"

    type(mock_motionmount).is_authenticated = PropertyMock(return_value=True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_PIN_INPUT.copy(),
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ZEROCONF_NAME

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT

    assert result["result"]
    assert result["result"].unique_id == ZEROCONF_MAC