def _get_camera_channels(
    hass: HomeAssistant,
    entry: UFPConfigEntry,
    data: ProtectData,
    ufp_device: UFPCamera | None = None,
) -> Generator[tuple[UFPCamera, CameraChannel, bool]]:
    """Get all the camera channels."""

    cameras = data.get_cameras() if ufp_device is None else [ufp_device]
    for camera in cameras:
        if not camera.channels:
            if ufp_device is None:
                # only warn on startup
                _LOGGER.warning(
                    "Camera does not have any channels: %s (id: %s)",
                    camera.display_name,
                    camera.id,
                )
            data.async_add_pending_camera_id(camera.id)
            continue

        is_default = True
        for channel in camera.channels:
            if channel.is_package:
                yield camera, channel, True
            elif channel.is_rtsp_enabled:
                yield camera, channel, is_default
                is_default = False

        # no RTSP enabled use first channel with no stream
        if is_default and not camera.is_third_party_camera:
            # Only create repair issue if RTSP is not disabled globally
            if not data.disable_stream:
                _create_rtsp_repair(hass, entry, data, camera)
            else:
                ir.async_delete_issue(hass, DOMAIN, f"rtsp_disabled_{camera.id}")
            yield camera, camera.channels[0], True
        else:
            ir.async_delete_issue(hass, DOMAIN, f"rtsp_disabled_{camera.id}")