async def test_discovery_match_by_service_data_uuid_when_format_changes(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test bluetooth discovery match by service_data_uuid when format changes."""
    mock_bt = [
        {
            "domain": "xiaomi_ble",
            "service_data_uuid": "0000fe95-0000-1000-8000-00805f9b34fb",
        },
        {
            "domain": "qingping",
            "service_data_uuid": "0000fdcd-0000-1000-8000-00805f9b34fb",
        },
    ]
    with patch(
        "homeassistant.components.bluetooth.async_get_bluetooth", return_value=mock_bt
    ):
        await async_setup_with_default_adapter(hass)

    with patch.object(hass.config_entries.flow, "async_init") as mock_config_flow:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        assert len(mock_bleak_scanner_start.mock_calls) == 1

        device = generate_ble_device("44:44:33:11:23:45", "lock")
        adv_without_service_data_uuid = generate_advertisement_data(
            local_name="Qingping Temp RH M",
            service_uuids=[],
            manufacturer_data={},
        )
        xiaomi_format_adv = generate_advertisement_data(
            local_name="Qingping Temp RH M",
            service_data={
                "0000fe95-0000-1000-8000-00805f9b34fb": b"0XH\x0b\x06\xa7%\x144-X\x08"
            },
        )
        qingping_format_adv = generate_advertisement_data(
            local_name="Qingping Temp RH M",
            service_data={
                "0000fdcd-0000-1000-8000-00805f9b34fb": (
                    b"\x08\x16\xa7%\x144-X\x01\x04\xdb\x00\xa6\x01\x02\x01d"
                )
            },
        )
        # 1st discovery should not generate a flow because the
        # service_data_uuid is not in the advertisement
        inject_advertisement(hass, device, adv_without_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 2nd discovery should generate a flow because the
        # service_data_uuid matches xiaomi format
        inject_advertisement(hass, device, xiaomi_format_adv)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "xiaomi_ble"
        mock_config_flow.reset_mock()

        # 4th discovery should generate a flow because the
        # service_data_uuid matches qingping format
        inject_advertisement(hass, device, qingping_format_adv)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "qingping"
        mock_config_flow.reset_mock()

        # 5th discovery should not generate a flow because the
        # we already saw an advertisement with the service_data_uuid
        inject_advertisement(hass, device, qingping_format_adv)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 6th discovery should not generate a flow because the
        # we already saw an advertisement with the service_data_uuid
        inject_advertisement(hass, device, xiaomi_format_adv)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()