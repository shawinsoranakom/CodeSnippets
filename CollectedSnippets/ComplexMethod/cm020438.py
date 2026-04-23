async def test_full_zeroconf_flow_implementation(
    hass: HomeAssistant,
    mock_motionmount: MagicMock,
) -> None:
    """Test the full zeroconf flow from start to finish."""
    type(mock_motionmount).name = PropertyMock(return_value=ZEROCONF_NAME)
    type(mock_motionmount).mac = PropertyMock(return_value=MAC)

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_TVM_SERVICE_INFO_V2)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ZEROCONF_NAME

    assert result["data"]
    assert result["data"][CONF_HOST] == ZEROCONF_HOSTNAME
    assert result["data"][CONF_PORT] == PORT
    assert result["data"][CONF_NAME] == ZEROCONF_NAME

    assert result["result"]
    assert result["result"].unique_id == ZEROCONF_MAC