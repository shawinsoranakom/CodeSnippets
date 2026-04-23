async def test_config_flow_zigbee_custom_other(hass: HomeAssistant) -> None:
    """Test flow with custom Zigbee installation type and Other selected."""
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
            user_input={"next_step_id": "zigbee_intent_custom"},
        )

        assert pick_result["type"] is FlowResultType.MENU
        assert pick_result["step_id"] == "zigbee_integration"

        pick_result = await hass.config_entries.flow.async_configure(
            pick_result["flow_id"],
            user_input={"next_step_id": "zigbee_integration_other"},
        )

        assert pick_result["type"] is FlowResultType.SHOW_PROGRESS
        assert pick_result["progress_action"] == "install_firmware"
        assert pick_result["step_id"] == "install_zigbee_firmware"

        show_z2m_result = await consume_progress_flow(
            hass,
            flow_id=pick_result["flow_id"],
            valid_step_ids=("install_zigbee_firmware",),
        )

        # After firmware installation, Z2M docs link is shown
        assert show_z2m_result["type"] is FlowResultType.FORM
        assert show_z2m_result["step_id"] == "show_z2m_docs_url"
        assert (
            show_z2m_result["description_placeholders"]["z2m_docs_url"]
            == Z2M_EMBER_DOCS_URL
        )

        # Submit the form to complete the flow
        create_result = await hass.config_entries.flow.async_configure(
            show_z2m_result["flow_id"],
            user_input={},
        )

        assert create_result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = create_result["result"]
    assert config_entry.data == {
        "firmware": "ezsp",
        "device": TEST_DEVICE,
        "hardware": TEST_HARDWARE_NAME,
    }

    flows = hass.config_entries.flow.async_progress()
    assert flows == []