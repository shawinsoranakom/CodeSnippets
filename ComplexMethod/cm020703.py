async def test_hardware_flow_strategy_advanced(hass: HomeAssistant) -> None:
    """Test advanced flow strategy for hardware flow."""
    data = {
        "name": "Yellow",
        "radio_type": "efr32",
        "port": {
            "path": "/dev/ttyAMA1",
            "baudrate": 115200,
            "flow_control": "hardware",
        },
        "flow_strategy": "advanced",
    }
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded", return_value=True
    ):
        result_hardware = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_HARDWARE}, data=data
        )

    assert result_hardware["type"] is FlowResultType.FORM
    assert result_hardware["step_id"] == "confirm"

    confirm_result = await hass.config_entries.flow.async_configure(
        result_hardware["flow_id"],
        user_input={},
    )

    assert confirm_result["type"] is FlowResultType.MENU
    assert confirm_result["step_id"] == "choose_formation_strategy"

    result_form = await hass.config_entries.flow.async_configure(
        confirm_result["flow_id"],
        user_input={"next_step_id": "form_new_network"},
    )

    result_create = await consume_progress_flow(
        hass,
        flow_id=result_form["flow_id"],
        valid_step_ids=("form_new_network",),
    )
    await hass.async_block_till_done()

    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["title"] == "Yellow"
    assert result_create["data"] == {
        CONF_DEVICE: {
            CONF_BAUDRATE: 115200,
            CONF_FLOW_CONTROL: "hardware",
            CONF_DEVICE_PATH: "/dev/ttyAMA1",
        },
        CONF_RADIO_TYPE: "ezsp",
    }