async def test_zeroconf_discovery(
    entry_name: str,
    unique_id: str,
    radio_type: RadioType,
    service_info: ZeroconfServiceInfo,
    hass: HomeAssistant,
) -> None:
    """Test zeroconf flow -- radio detected."""
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=service_info
    )
    assert result_init["step_id"] == "confirm"

    # Confirm port settings
    result_confirm = await hass.config_entries.flow.async_configure(
        result_init["flow_id"], user_input={}
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
    assert result_form["title"] == entry_name
    assert result_form["context"]["unique_id"] == unique_id
    assert result_form["data"] == {
        CONF_DEVICE: {
            CONF_BAUDRATE: 115200,
            CONF_FLOW_CONTROL: None,
            CONF_DEVICE_PATH: "socket://192.168.1.200:6638",
        },
        CONF_RADIO_TYPE: radio_type.name,
    }