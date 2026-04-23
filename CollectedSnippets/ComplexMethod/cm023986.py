async def test_discovery_match_by_manufacturer_id_and_manufacturer_data_start(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test bluetooth discovery match by manufacturer_id and manufacturer_data_start."""
    mock_bt = [
        {
            "domain": "homekit_controller",
            "manufacturer_id": 76,
            "manufacturer_data_start": [0x06, 0x02, 0x03],
        }
    ]
    with patch(
        "homeassistant.components.bluetooth.async_get_bluetooth", return_value=mock_bt
    ):
        await async_setup_with_default_adapter(hass)

    with patch.object(hass.config_entries.flow, "async_init") as mock_config_flow:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        assert len(mock_bleak_scanner_start.mock_calls) == 1

        hkc_device = generate_ble_device("44:44:33:11:23:45", "lock")
        hkc_adv_no_mfr_data = generate_advertisement_data(
            local_name="lock",
            service_uuids=[],
            manufacturer_data={},
        )
        hkc_adv = generate_advertisement_data(
            local_name="lock",
            service_uuids=[],
            manufacturer_data={76: b"\x06\x02\x03\x99"},
        )

        # 1st discovery with no manufacturer data
        # should not trigger config flow
        inject_advertisement(hass, hkc_device, hkc_adv_no_mfr_data)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 2nd discovery with manufacturer data
        # should trigger a config flow
        inject_advertisement(hass, hkc_device, hkc_adv)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "homekit_controller"
        mock_config_flow.reset_mock()

        # 3rd discovery should not generate another flow
        inject_advertisement(hass, hkc_device, hkc_adv)
        await hass.async_block_till_done()

        assert len(mock_config_flow.mock_calls) == 0

        mock_config_flow.reset_mock()
        not_hkc_device = generate_ble_device("44:44:33:11:23:21", "lock")
        not_hkc_adv = generate_advertisement_data(
            local_name="lock", service_uuids=[], manufacturer_data={76: b"\x02"}
        )

        inject_advertisement(hass, not_hkc_device, not_hkc_adv)
        await hass.async_block_till_done()

        assert len(mock_config_flow.mock_calls) == 0
        not_apple_device = generate_ble_device("44:44:33:11:23:23", "lock")
        not_apple_adv = generate_advertisement_data(
            local_name="lock", service_uuids=[], manufacturer_data={21: b"\x02"}
        )

        inject_advertisement(hass, not_apple_device, not_apple_adv)
        await hass.async_block_till_done()

        assert len(mock_config_flow.mock_calls) == 0