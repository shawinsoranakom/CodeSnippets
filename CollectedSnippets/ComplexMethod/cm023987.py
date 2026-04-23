async def test_discovery_match_by_service_data_uuid_then_others(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test bluetooth discovery match by service_data_uuid and then other fields."""
    mock_bt = [
        {
            "domain": "my_domain",
            "service_data_uuid": "0000fd3d-0000-1000-8000-00805f9b34fb",
        },
        {
            "domain": "my_domain",
            "service_uuid": "0000fd3d-0000-1000-8000-00805f9b34fc",
        },
        {
            "domain": "other_domain",
            "manufacturer_id": 323,
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
            local_name="lock",
            service_uuids=[],
            manufacturer_data={},
        )
        adv_with_mfr_data = generate_advertisement_data(
            local_name="lock",
            service_uuids=[],
            manufacturer_data={323: b"\x01\x02\x03"},
            service_data={},
        )
        adv_with_service_data_uuid = generate_advertisement_data(
            local_name="lock",
            service_uuids=[],
            manufacturer_data={},
            service_data={"0000fd3d-0000-1000-8000-00805f9b34fb": b"\x01\x02\x03"},
        )
        adv_with_service_data_uuid_and_mfr_data = generate_advertisement_data(
            local_name="lock",
            service_uuids=[],
            manufacturer_data={323: b"\x01\x02\x03"},
            service_data={"0000fd3d-0000-1000-8000-00805f9b34fb": b"\x01\x02\x03"},
        )
        adv_with_service_data_uuid_and_mfr_data_and_service_uuid = (
            generate_advertisement_data(
                local_name="lock",
                manufacturer_data={323: b"\x01\x02\x03"},
                service_data={"0000fd3d-0000-1000-8000-00805f9b34fb": b"\x01\x02\x03"},
                service_uuids=["0000fd3d-0000-1000-8000-00805f9b34fd"],
            )
        )
        adv_with_service_uuid = generate_advertisement_data(
            local_name="lock",
            manufacturer_data={},
            service_data={},
            service_uuids=["0000fd3d-0000-1000-8000-00805f9b34fd"],
        )
        # 1st discovery should not generate a flow because the
        # service_data_uuid is not in the advertisement
        inject_advertisement(hass, device, adv_without_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 2nd discovery should not generate a flow because the
        # service_data_uuid is not in the advertisement
        inject_advertisement(hass, device, adv_without_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 3rd discovery should generate a flow because the
        # manufacturer_data is in the advertisement
        inject_advertisement(hass, device, adv_with_mfr_data)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "other_domain"
        mock_config_flow.reset_mock()

        # 4th discovery should generate a flow because the
        # service_data_uuid is in the advertisement and
        # we never saw a service_data_uuid before
        inject_advertisement(hass, device, adv_with_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "my_domain"
        mock_config_flow.reset_mock()

        # 5th discovery should not generate a flow because the
        # we already saw an advertisement with the service_data_uuid
        inject_advertisement(hass, device, adv_with_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0

        # 6th discovery should not generate a flow because the
        # manufacturer_data is in the advertisement
        # and we saw manufacturer_data before
        inject_advertisement(hass, device, adv_with_service_data_uuid_and_mfr_data)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 7th discovery should generate a flow because the
        # service_uuids is in the advertisement
        # and we never saw service_uuids before
        inject_advertisement(
            hass, device, adv_with_service_data_uuid_and_mfr_data_and_service_uuid
        )
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 2
        assert {
            mock_config_flow.mock_calls[0][1][0],
            mock_config_flow.mock_calls[1][1][0],
        } == {"my_domain", "other_domain"}
        mock_config_flow.reset_mock()

        # 8th discovery should not generate a flow
        # since all fields have been seen at this point
        inject_advertisement(
            hass, device, adv_with_service_data_uuid_and_mfr_data_and_service_uuid
        )
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0
        mock_config_flow.reset_mock()

        # 9th discovery should not generate a flow
        # since all fields have been seen at this point
        inject_advertisement(hass, device, adv_with_service_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0

        # 10th discovery should not generate a flow
        # since all fields have been seen at this point
        inject_advertisement(hass, device, adv_with_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0

        # 11th discovery should not generate a flow
        # since all fields have been seen at this point
        inject_advertisement(hass, device, adv_without_service_data_uuid)
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 0