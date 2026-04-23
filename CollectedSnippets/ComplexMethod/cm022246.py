async def test_user_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user form."""

    with patch(
        "homeassistant.components.hue_ble.config_flow.bluetooth.async_discovered_service_info",
        return_value=[NOT_HUE_BLE_DISCOVERY_INFO, HUE_BLE_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"].schema[CONF_MAC].container == {
        HUE_BLE_SERVICE_INFO.address: (
            f"{HUE_BLE_SERVICE_INFO.name} ({HUE_BLE_SERVICE_INFO.address})"
        ),
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: HUE_BLE_SERVICE_INFO.address},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        CONF_NAME: TEST_DEVICE_NAME,
        CONF_MAC: TEST_DEVICE_MAC,
        "url_pairing_mode": URL_PAIRING_MODE,
        "url_factory_reset": URL_FACTORY_RESET,
    }

    with (
        patch(
            "homeassistant.components.hue_ble.config_flow.async_ble_device_from_address",
            return_value=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.async_scanner_count",
            return_value=1,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.connect",
            side_effect=[True],
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.poll_state",
            side_effect=[True],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_DEVICE_NAME
    assert result["result"].unique_id == dr.format_mac(TEST_DEVICE_MAC)
    assert result["result"].data == {}

    assert len(mock_setup_entry.mock_calls) == 1