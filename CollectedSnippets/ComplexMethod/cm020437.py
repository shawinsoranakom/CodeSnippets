async def test_full_user_flow_implementation(
    hass: HomeAssistant,
    mock_motionmount: MagicMock,
) -> None:
    """Test the full manual user flow from start to finish."""
    type(mock_motionmount).name = PropertyMock(return_value=ZEROCONF_NAME)
    type(mock_motionmount).mac = PropertyMock(return_value=MAC)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_INPUT.copy(),
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ZEROCONF_NAME

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT

    assert result["result"]
    assert result["result"].unique_id == ZEROCONF_MAC