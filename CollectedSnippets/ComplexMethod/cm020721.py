async def test_update_release_notes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup_zha: Callable[..., Coroutine[None]],
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test ZHA update platform release notes."""
    await setup_zha()
    zha_device, _, _, _ = await setup_test_data(hass, zigpy_device_mock)

    zha_lib_entity = next(
        e
        for e in zha_device.device.platform_entities.values()
        if isinstance(e, ZhaFirmwareUpdateEntity)
    )
    zha_lib_entity._attr_release_notes = "Some lengthy release notes"
    zha_lib_entity.maybe_emit_state_changed_event()
    await hass.async_block_till_done()

    entity_id = find_entity_id(Platform.UPDATE, zha_device, hass)
    assert entity_id is not None

    ws_client = await hass_ws_client(hass)

    # Mains-powered devices
    with patch(
        "zha.zigbee.device.Device.is_mains_powered", PropertyMock(return_value=True)
    ):
        await ws_client.send_json(
            {
                "id": 1,
                "type": "update/release_notes",
                "entity_id": entity_id,
            }
        )

        result = await ws_client.receive_json()
        assert result["success"] is True
        assert "Some lengthy release notes" in result["result"]
        assert OTA_MESSAGE_RELIABILITY in result["result"]
        assert OTA_MESSAGE_BATTERY_POWERED not in result["result"]

    # Battery-powered devices
    with patch(
        "zha.zigbee.device.Device.is_mains_powered", PropertyMock(return_value=False)
    ):
        await ws_client.send_json(
            {
                "id": 2,
                "type": "update/release_notes",
                "entity_id": entity_id,
            }
        )

        result = await ws_client.receive_json()
        assert result["success"] is True
        assert "Some lengthy release notes" in result["result"]
        assert OTA_MESSAGE_RELIABILITY in result["result"]
        assert OTA_MESSAGE_BATTERY_POWERED in result["result"]