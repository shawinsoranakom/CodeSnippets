def setup_mock_onvif_camera(
    mock_onvif_camera,
    with_h264=True,
    two_profiles=False,
    with_interfaces=True,
    with_interfaces_not_implemented=False,
    with_serial=True,
    profiles_transient_failure=False,
    auth_fail=False,
    update_xaddrs_fail=False,
    no_profiles=False,
    auth_failure=False,
    wrong_port=False,
):
    """Prepare mock onvif.ONVIFCamera."""
    devicemgmt = MagicMock()

    device_info = MagicMock()
    device_info.SerialNumber = SERIAL_NUMBER if with_serial else None

    devicemgmt.GetDeviceInformation = AsyncMock(return_value=device_info)

    interface = MagicMock()
    interface.Enabled = True
    interface.Info.HwAddress = MAC

    if with_interfaces_not_implemented:
        devicemgmt.GetNetworkInterfaces = AsyncMock(
            side_effect=Fault("not implemented")
        )
    else:
        devicemgmt.GetNetworkInterfaces = AsyncMock(
            return_value=[interface] if with_interfaces else []
        )

    media_service = MagicMock()

    profile1 = MagicMock()
    profile1.VideoEncoderConfiguration.Encoding = "H264" if with_h264 else "MJPEG"
    profile2 = MagicMock()
    profile2.VideoEncoderConfiguration.Encoding = "H264" if two_profiles else "MJPEG"

    if auth_fail:
        media_service.GetProfiles = AsyncMock(side_effect=Fault("Authority failure"))
    elif profiles_transient_failure:
        media_service.GetProfiles = AsyncMock(side_effect=Fault("camera not ready"))
    elif no_profiles:
        media_service.GetProfiles = AsyncMock(return_value=[])
    else:
        media_service.GetProfiles = AsyncMock(return_value=[profile1, profile2])

    if wrong_port:
        mock_onvif_camera.update_xaddrs = AsyncMock(side_effect=AttributeError)
    elif auth_failure:
        mock_onvif_camera.update_xaddrs = AsyncMock(
            side_effect=Fault(
                "not authorized", subcodes=[MagicMock(text="NotAuthorized")]
            )
        )
    elif update_xaddrs_fail:
        mock_onvif_camera.update_xaddrs = AsyncMock(
            side_effect=ONVIFError("camera not ready")
        )
    else:
        mock_onvif_camera.update_xaddrs = AsyncMock(return_value=True)
    mock_onvif_camera.create_devicemgmt_service = AsyncMock(return_value=devicemgmt)
    mock_onvif_camera.create_media_service = AsyncMock(return_value=media_service)
    mock_onvif_camera.close = AsyncMock(return_value=None)
    mock_onvif_camera.xaddrs = {}
    mock_onvif_camera.services = {}

    def mock_constructor(
        host,
        port,
        user,
        passwd,
        wsdl_dir,
        encrypt=True,
        no_cache=False,
        adjust_time=False,
        transport=None,
    ):
        """Fake the controller constructor."""
        return mock_onvif_camera

    mock_onvif_camera.side_effect = mock_constructor