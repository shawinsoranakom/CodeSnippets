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