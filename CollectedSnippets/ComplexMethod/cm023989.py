async def test_discovery_match_first_by_service_uuid_and_then_manufacturer_id(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test bluetooth discovery matches twice for service_uuid and then manufacturer_id."""
    mock_bt = [
        {
            "domain": "my_domain",
            "manufacturer_id": 76,
        },
        {
            "domain": "my_domain",
            "service_uuid": "0000fd3d-0000-1000-8000-00805f9b34fc",
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
        adv_service_uuids = generate_advertisement_data(
            local_name="lock",
            service_uuids=["0000fd3d-0000-1000-8000-00805f9b34fc"],
            manufacturer_data={},
        )
        adv_manufacturer_data = generate_advertisement_data(
            local_name="lock",
            service_uuids=[],
            manufacturer_data={76: b"\x06\x02\x03\x99"},
        )

        # 1st discovery with matches service_uuid
        # should trigger config flow
        inject_advertisement(hass, device, adv_service_uuids)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "my_domain"
        mock_config_flow.reset_mock()

        # 2nd discovery with manufacturer data
        # should trigger a config flow
        inject_advertisement(hass, device, adv_manufacturer_data)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "my_domain"
        mock_config_flow.reset_mock()

        # 3rd discovery should not generate another flow
        inject_advertisement(hass, device, adv_service_uuids)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0

        # 4th discovery should not generate another flow
        inject_advertisement(hass, device, adv_manufacturer_data)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0