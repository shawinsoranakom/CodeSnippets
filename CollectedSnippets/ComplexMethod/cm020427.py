async def test_user_response_error_single_device_new_ce_new_pro(
    hass: HomeAssistant,
    mock_motionmount: MagicMock,
) -> None:
    """Test that the flow creates an entry when there is a response error."""
    type(mock_motionmount).name = PropertyMock(return_value=ZEROCONF_NAME)
    type(mock_motionmount).mac = PropertyMock(return_value=MAC)

    user_input = MOCK_USER_INPUT.copy()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ZEROCONF_NAME

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT

    assert result["result"]
    assert result["result"].unique_id == ZEROCONF_MAC