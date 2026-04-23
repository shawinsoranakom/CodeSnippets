async def test_firmware_update_raises(
    hass: HomeAssistant,
    setup_zha: Callable[..., Coroutine[None]],
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test ZHA update platform - firmware update raises."""
    await setup_zha()
    zha_device, ota_cluster, fw_image, installed_fw_version = await setup_test_data(
        hass, zigpy_device_mock
    )

    entity_id = find_entity_id(Platform.UPDATE, zha_device, hass)
    assert entity_id is not None

    assert hass.states.get(entity_id).state == STATE_UNKNOWN

    # simulate an image available notification
    await ota_cluster._handle_query_next_image(
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

    async def endpoint_reply(cluster, sequence, data, **kwargs):
        if cluster == general.Ota.cluster_id:
            _hdr, cmd = ota_cluster.deserialize(data)
            if isinstance(cmd, general.Ota.ImageNotifyCommand):
                zha_device.device.device.packet_received(
                    make_packet(
                        zha_device.device.device,
                        ota_cluster,
                        general.Ota.ServerCommandDefs.query_next_image.name,
                        field_control=general.Ota.QueryNextImageCommand.FieldControl.HardwareVersion,
                        manufacturer_code=fw_image.firmware.header.manufacturer_id,
                        image_type=fw_image.firmware.header.image_type,
                        current_file_version=fw_image.firmware.header.file_version - 10,
                        hardware_version=1,
                    )
                )
            elif isinstance(
                cmd, general.Ota.ClientCommandDefs.query_next_image_response.schema
            ):
                if cmd.status == foundation.Status.NO_IMAGE_AVAILABLE:
                    return

                assert cmd.status == foundation.Status.SUCCESS
                assert cmd.manufacturer_code == fw_image.firmware.header.manufacturer_id
                assert cmd.image_type == fw_image.firmware.header.image_type
                assert cmd.file_version == fw_image.firmware.header.file_version
                assert cmd.image_size == fw_image.firmware.header.image_size
                raise DeliveryError("failed to deliver")

    ota_cluster.endpoint.reply = AsyncMock(side_effect=endpoint_reply)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_ENTITY_ID: entity_id,
            },
            blocking=True,
        )

    with (
        patch(
            "zigpy.device.Device.update_firmware",
            AsyncMock(side_effect=DeliveryError("failed to deliver")),
        ),
        pytest.raises(HomeAssistantError),
    ):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_ENTITY_ID: entity_id,
            },
            blocking=True,
        )