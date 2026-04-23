async def test_firmware_update_notification_from_zigpy(
    hass: HomeAssistant,
    setup_zha: Callable[..., Coroutine[None]],
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test ZHA update platform - firmware update notification."""
    await setup_zha()
    zha_device, cluster, fw_image, installed_fw_version = await setup_test_data(
        hass,
        zigpy_device_mock,
    )

    entity_id = find_entity_id(Platform.UPDATE, zha_device, hass)
    assert entity_id is not None

    assert hass.states.get(entity_id).state == STATE_UNKNOWN

    # simulate an image available notification
    await cluster._handle_query_next_image(
        foundation.ZCLHeader.cluster(
            tsn=0x12, command_id=general.Ota.ServerCommandDefs.query_next_image.id
        ),
        general.QueryNextImageCommand(
            fw_image.firmware.header.field_control,
            zha_device.device.manufacturer_code,
            fw_image.firmware.header.image_type,
            installed_fw_version,
            fw_image.firmware.header.header_version,
        ),
    )

    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attrs = state.attributes
    assert attrs[ATTR_INSTALLED_VERSION] == f"0x{installed_fw_version:08x}"
    assert attrs[ATTR_IN_PROGRESS] is False
    assert attrs[ATTR_UPDATE_PERCENTAGE] is None
    assert (
        attrs[ATTR_LATEST_VERSION] == f"0x{fw_image.firmware.header.file_version:08x}"
    )