async def test_zeroconf_authentication_needed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_motionmount: MagicMock,
) -> None:
    """Test that authentication is requested when needed."""
    type(mock_motionmount).mac = PropertyMock(return_value=MAC)
    type(mock_motionmount).is_authenticated = PropertyMock(return_value=False)

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_TVM_SERVICE_INFO_V2)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"

    # Now simulate the user entered the correct pin to finalize the test
    type(mock_motionmount).is_authenticated = PropertyMock(return_value=True)
    type(mock_motionmount).can_authenticate = PropertyMock(return_value=True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_PIN_INPUT.copy(),
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ZEROCONF_NAME

    assert result["data"]
    assert result["data"][CONF_HOST] == ZEROCONF_HOSTNAME
    assert result["data"][CONF_PORT] == PORT
    assert result["data"][CONF_NAME] == ZEROCONF_NAME

    assert result["result"]
    assert result["result"].unique_id == ZEROCONF_MAC