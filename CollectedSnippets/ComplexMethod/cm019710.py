async def test_config_flow_zigbee_recommended(hass: HomeAssistant) -> None:
    """Test flow with recommended Zigbee installation type."""
    init_result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": "hardware"}
    )

    assert init_result["type"] is FlowResultType.MENU
    assert init_result["step_id"] == "pick_firmware"

    with mock_firmware_info(
        probe_app_type=ApplicationType.SPINEL,
        flash_app_type=ApplicationType.EZSP,
    ):
        # Pick the menu option: we are flashing the firmware
        pick_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            user_input={"next_step_id": STEP_PICK_FIRMWARE_ZIGBEE},
        )

        assert pick_result["type"] is FlowResultType.MENU
        assert pick_result["step_id"] == "zigbee_installation_type"

        pick_result = await hass.config_entries.flow.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_intent_recommended"},
        )

        assert pick_result["type"] is FlowResultType.SHOW_PROGRESS
        assert pick_result["progress_action"] == "install_firmware"
        assert pick_result["step_id"] == "install_zigbee_firmware"

        create_result = await consume_progress_flow(
            hass,
            flow_id=pick_result["flow_id"],
            valid_step_ids=("install_zigbee_firmware",),
        )

        assert create_result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = create_result["result"]
    assert config_entry.data == {
        "firmware": "ezsp",
        "device": TEST_DEVICE,
        "hardware": TEST_HARDWARE_NAME,
    }

    # Ensure a ZHA discovery flow has been created
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    zha_flow = flows[0]
    assert zha_flow["handler"] == "zha"
    assert zha_flow["context"]["source"] == "hardware"
    assert zha_flow["step_id"] == "confirm"

    progress_zha_flows = hass.config_entries.flow._async_progress_by_handler(
        handler="zha",
        match_context=None,
    )

    assert len(progress_zha_flows) == 1

    progress_zha_flow = progress_zha_flows[0]
    assert progress_zha_flow.init_data == {
        "name": "Some Hardware Name",
        "port": {
            "path": "/dev/SomeDevice123",
            "baudrate": 115200,
            "flow_control": "hardware",
        },
        "radio_type": "ezsp",
        "flow_strategy": "recommended",
    }