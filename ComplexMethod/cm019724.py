async def test_config_flow_firmware_index_download_fails_and_required(
    hass: HomeAssistant,
) -> None:
    """Test flow aborts if OTA index download fails and install is required."""
    init_result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": "hardware"}
    )

    assert init_result["type"] is FlowResultType.MENU
    assert init_result["step_id"] == "pick_firmware"

    with mock_firmware_info(
        # The wrong firmware is installed, so a new install is required
        probe_app_type=ApplicationType.SPINEL,
    ) as mock_update_client:
        mock_update_client.async_update_data.side_effect = ClientError()

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

        assert pick_result["type"] is FlowResultType.ABORT
        assert pick_result["reason"] == "fw_download_failed"
        assert pick_result["description_placeholders"] == {
            "firmware_name": "Zigbee",
            "model": TEST_HARDWARE_NAME,
            "firmware_type": "spinel",
        }