async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="a0:d9:5a:57:0b:00",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.medcom_ble.config_flow.async_discovered_service_info",
        return_value=[MEDCOM_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Verify the ignored device is in the dropdown
    assert "a0:d9:5a:57:0b:00" in result["data_schema"].schema[CONF_ADDRESS].container

    with (
        patch_async_ble_device_from_address(MEDCOM_SERVICE_INFO),
        patch_medcom_ble(
            MedcomBleDevice(
                manufacturer="International Medcom",
                model="Inspector BLE",
                model_raw="Inspector-BLE",
                name="Inspector BLE",
                identifier="a0d95a570b00",
            )
        ),
        patch(
            "homeassistant.components.medcom_ble.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "a0:d9:5a:57:0b:00"}
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "InspectorBLE-D9A0"
    assert result2["data"] == {}
    assert result2["result"].unique_id == "a0:d9:5a:57:0b:00"