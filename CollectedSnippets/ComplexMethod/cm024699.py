async def test_bluetooth_valid_device_discovery_unpaired(
    hass: HomeAssistant, controller
) -> None:
    """Test bluetooth discovery with a homekit device and discovery works."""
    setup_mock_accessory(controller)
    storage = await async_get_entity_storage(hass)

    with patch(
        "homeassistant.components.homekit_controller.config_flow.aiohomekit_const.BLE_TRANSPORT_SUPPORTED",
        True,
    ):
        result = await hass.config_entries.flow.async_init(
            "homekit_controller",
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=HK_BLUETOOTH_SERVICE_INFO_DISCOVERED_UNPAIRED,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert storage.get_map("00:00:00:00:00:00") is None

    assert get_flow_context(hass, result) == {
        "source": config_entries.SOURCE_BLUETOOTH,
        "unique_id": "00:00:00:00:00:00",
        "title_placeholders": {"name": "TestDevice", "category": "Other"},
    }

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result2["type"] is FlowResultType.FORM
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], user_input={"pairing_code": "111-22-333"}
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Koogeek-LS1-20833F"
    assert result3["data"] == {}

    assert storage.get_map("00:00:00:00:00:00") is not None