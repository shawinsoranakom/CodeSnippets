async def endpoint_reply(cluster, sequence, data, **kwargs):
        nonlocal ota_completed
        if cluster == general.Ota.cluster_id:
            _hdr, cmd = ota_cluster.deserialize(data)
            if isinstance(cmd, general.Ota.ImageNotifyCommand):
                if ota_completed:
                    # Post-OTA image_notify: ignore or don't respond
                    return

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
                # After a successful OTA, zigpy sends a post-OTA image_notify
                # which triggers a query_next_image -> NO_IMAGE_AVAILABLE exchange
                if cmd.status == foundation.Status.NO_IMAGE_AVAILABLE:
                    assert ota_completed
                    return

                assert cmd.status == foundation.Status.SUCCESS
                assert cmd.manufacturer_code == fw_image.firmware.header.manufacturer_id
                assert cmd.image_type == fw_image.firmware.header.image_type
                assert cmd.file_version == fw_image.firmware.header.file_version
                assert cmd.image_size == fw_image.firmware.header.image_size
                zha_device.device.device.packet_received(
                    make_packet(
                        zha_device.device.device,
                        ota_cluster,
                        general.Ota.ServerCommandDefs.image_block.name,
                        field_control=general.Ota.ImageBlockCommand.FieldControl.RequestNodeAddr,
                        manufacturer_code=fw_image.firmware.header.manufacturer_id,
                        image_type=fw_image.firmware.header.image_type,
                        file_version=fw_image.firmware.header.file_version,
                        file_offset=0,
                        maximum_data_size=40,
                        request_node_addr=zha_device.device.device.ieee,
                    )
                )
            elif isinstance(
                cmd, general.Ota.ClientCommandDefs.image_block_response.schema
            ):
                if cmd.file_offset == 0:
                    assert cmd.status == foundation.Status.SUCCESS
                    assert (
                        cmd.manufacturer_code
                        == fw_image.firmware.header.manufacturer_id
                    )
                    assert cmd.image_type == fw_image.firmware.header.image_type
                    assert cmd.file_version == fw_image.firmware.header.file_version
                    assert cmd.file_offset == 0
                    assert cmd.image_data == fw_image.firmware.serialize()[0:40]
                    zha_device.device.device.packet_received(
                        make_packet(
                            zha_device.device.device,
                            ota_cluster,
                            general.Ota.ServerCommandDefs.image_block.name,
                            field_control=general.Ota.ImageBlockCommand.FieldControl.RequestNodeAddr,
                            manufacturer_code=fw_image.firmware.header.manufacturer_id,
                            image_type=fw_image.firmware.header.image_type,
                            file_version=fw_image.firmware.header.file_version,
                            file_offset=40,
                            maximum_data_size=40,
                            request_node_addr=zha_device.device.device.ieee,
                        )
                    )
                elif cmd.file_offset == 40:
                    assert cmd.status == foundation.Status.SUCCESS
                    assert (
                        cmd.manufacturer_code
                        == fw_image.firmware.header.manufacturer_id
                    )
                    assert cmd.image_type == fw_image.firmware.header.image_type
                    assert cmd.file_version == fw_image.firmware.header.file_version
                    assert cmd.file_offset == 40
                    assert cmd.image_data == fw_image.firmware.serialize()[40:70]

                    # make sure the state machine gets progress reports
                    state = hass.states.get(entity_id)
                    assert state.state == STATE_ON
                    attrs = state.attributes
                    assert (
                        attrs[ATTR_INSTALLED_VERSION] == f"0x{installed_fw_version:08x}"
                    )
                    assert attrs[ATTR_IN_PROGRESS] is True
                    assert attrs[ATTR_UPDATE_PERCENTAGE] == pytest.approx(100 * 40 / 70)
                    assert (
                        attrs[ATTR_LATEST_VERSION]
                        == f"0x{fw_image.firmware.header.file_version:08x}"
                    )

                    zha_device.device.device.packet_received(
                        make_packet(
                            zha_device.device.device,
                            ota_cluster,
                            general.Ota.ServerCommandDefs.upgrade_end.name,
                            status=foundation.Status.SUCCESS,
                            manufacturer_code=fw_image.firmware.header.manufacturer_id,
                            image_type=fw_image.firmware.header.image_type,
                            file_version=fw_image.firmware.header.file_version,
                        )
                    )

            elif isinstance(
                cmd, general.Ota.ClientCommandDefs.upgrade_end_response.schema
            ):
                assert cmd.manufacturer_code == fw_image.firmware.header.manufacturer_id
                assert cmd.image_type == fw_image.firmware.header.image_type
                assert cmd.file_version == fw_image.firmware.header.file_version
                assert cmd.current_time == 0
                assert cmd.upgrade_time == 0

                ota_completed = True

                def read_new_fw_version(*args, **kwargs):
                    ota_cluster.update_attribute(
                        attrid=general.Ota.AttributeDefs.current_file_version.id,
                        value=fw_image.firmware.header.file_version,
                    )
                    return {
                        general.Ota.AttributeDefs.current_file_version.id: (
                            fw_image.firmware.header.file_version
                        )
                    }, {}

                ota_cluster.read_attributes.side_effect = read_new_fw_version