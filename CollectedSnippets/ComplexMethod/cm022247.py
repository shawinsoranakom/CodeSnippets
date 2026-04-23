async def test_user_form_exception(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_return_device: BLEDevice | None,
    mock_scanner_count: int,
    mock_connect: Exception | None,
    mock_support_on_off: bool,
    mock_poll_state: Exception | None,
    error: Error,
) -> None:
    """Test user form with errors."""

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

    with (
        patch(
            "homeassistant.components.hue_ble.config_flow.async_ble_device_from_address",
            return_value=mock_return_device,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.async_scanner_count",
            return_value=mock_scanner_count,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.connect",
            side_effect=[mock_connect],
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.supports_on_off",
            new_callable=PropertyMock,
            return_value=mock_support_on_off,
        ),
        patch(
            "homeassistant.components.hue_ble.config_flow.HueBleLight.poll_state",
            side_effect=[mock_poll_state],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error.value}

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