async def test_firmware_update_poll_after_reload(
    hass: HomeAssistant,
    setup_zha: Callable[..., Coroutine[None]],
    config_entry: MockConfigEntry,
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test polling a ZHA update entity still works after reloading ZHA."""
    await setup_zha()
    await async_setup_component(hass, HA_DOMAIN, {})

    zha_data = get_zha_data(hass)
    coordinator_before = zha_data.update_coordinator
    assert coordinator_before is not None

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator_after = get_zha_data(hass).update_coordinator
    assert coordinator_after is not None
    assert coordinator_after is not coordinator_before

    zha_device, _, _, _ = await setup_test_data(hass, zigpy_device_mock)
    entity_id = find_entity_id(Platform.UPDATE, zha_device, hass)
    assert entity_id is not None

    with patch("zigpy.ota.OTA.broadcast_notify") as mock_broadcast_notify:
        await hass.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            service_data={ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        assert mock_broadcast_notify.await_count == 1
        assert mock_broadcast_notify.call_args_list[0] == call(jitter=100)