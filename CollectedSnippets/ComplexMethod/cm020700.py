async def test_legacy_zeroconf_discovery_zigate(
    setup_entry_mock, hass: HomeAssistant
) -> None:
    """Test zeroconf flow -- zigate radio detected."""
    service_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.200"),
        ip_addresses=[ip_address("192.168.1.200")],
        hostname="_zigate-zigbee-gateway.local.",
        name="some name._zigate-zigbee-gateway._tcp.local.",
        port=1234,
        properties={},
        type="mock_type",
    )
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=service_info
    )
    assert result_init["step_id"] == "confirm"

    # Confirm the radio is deprecated
    result_confirm_deprecated = await hass.config_entries.flow.async_configure(
        result_init["flow_id"], user_input={}
    )
    assert result_confirm_deprecated["step_id"] == "verify_radio"
    assert "ZiGate" in result_confirm_deprecated["description_placeholders"]["name"]

    # Confirm port settings
    result_confirm = await hass.config_entries.flow.async_configure(
        result_confirm_deprecated["flow_id"], user_input={}
    )

    assert result_confirm["type"] is FlowResultType.MENU
    assert result_confirm["step_id"] == "choose_setup_strategy"

    result_setup = await hass.config_entries.flow.async_configure(
        result_confirm["flow_id"],
        user_input={"next_step_id": config_flow.SETUP_STRATEGY_RECOMMENDED},
    )

    result_form = await consume_progress_flow(
        hass,
        flow_id=result_setup["flow_id"],
        valid_step_ids=("form_new_network",),
    )
    await hass.async_block_till_done()

    assert result_form["type"] is FlowResultType.CREATE_ENTRY
    assert result_form["title"] == "some name"
    assert result_form["data"] == {
        CONF_DEVICE: {
            CONF_DEVICE_PATH: "socket://192.168.1.200:1234",
            CONF_BAUDRATE: 115200,
            CONF_FLOW_CONTROL: None,
        },
        CONF_RADIO_TYPE: "zigate",
    }