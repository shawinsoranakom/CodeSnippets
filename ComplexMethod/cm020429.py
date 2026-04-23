async def test_show_zeroconf_form_new_ce_old_pro(
    hass: HomeAssistant,
    mock_motionmount: MagicMock,
) -> None:
    """Test that the zeroconf confirmation form is served."""
    type(mock_motionmount).mac = PropertyMock(return_value=b"\x00\x00\x00\x00\x00\x00")

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_TVM_SERVICE_INFO_V1)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"] == {CONF_NAME: "My MotionMount"}

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
    assert result["result"].unique_id is None