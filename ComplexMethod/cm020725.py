async def test_cover_failures(
    hass: HomeAssistant,
    setup_zha: Callable[..., Coroutine[None]],
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test ZHA cover platform failure cases."""
    await setup_zha()
    gateway = get_zha_gateway(hass)
    gateway_proxy: ZHAGatewayProxy = get_zha_gateway_proxy(hass)

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_PROFILE: zha.PROFILE_ID,
                SIG_EP_TYPE: zha.DeviceType.WINDOW_COVERING_DEVICE,
                SIG_EP_INPUT: [closures.WindowCovering.cluster_id],
                SIG_EP_OUTPUT: [],
            }
        },
    )
    # load up cover domain
    cluster = zigpy_device.endpoints[1].window_covering
    cluster.PLUGGED_ATTR_READS = {
        WCAttrs.current_position_tilt_percentage.name: 100,
        WCAttrs.window_covering_type.name: WCT.Tilt_blind_tilt_and_lift,
    }
    update_attribute_cache(cluster)

    gateway.get_or_create_device(zigpy_device)
    await gateway.async_device_initialized(zigpy_device)
    await hass.async_block_till_done(wait_background_tasks=True)

    zha_device_proxy: ZHADeviceProxy = gateway_proxy.get_device_proxy(zigpy_device.ieee)
    entity_id = find_entity_id(Platform.COVER, zha_device_proxy, hass)
    assert entity_id is not None

    # test that the state has changed from unavailable to closed
    await send_attributes_report(
        hass,
        cluster,
        {
            WCAttrs.current_position_lift_percentage.id: 100,
            WCAttrs.current_position_tilt_percentage.id: 100,
        },
    )
    assert hass.states.get(entity_id).state == CoverState.CLOSED

    # test that it opens
    await send_attributes_report(
        hass,
        cluster,
        {
            WCAttrs.current_position_lift_percentage.id: 0,
            WCAttrs.current_position_tilt_percentage.id: 0,
        },
    )
    assert hass.states.get(entity_id).state == CoverState.OPEN

    # close from UI
    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.down_close.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to close cover"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_CLOSE_COVER,
                {"entity_id": entity_id},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.down_close.id
        )

    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to close cover tilt"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_CLOSE_COVER_TILT,
                {"entity_id": entity_id},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id
        )

    # open from UI
    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.up_open.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to open cover"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_OPEN_COVER,
                {"entity_id": entity_id},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.up_open.id
        )

    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to open cover tilt"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_OPEN_COVER_TILT,
                {"entity_id": entity_id},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id
        )

    # set position UI
    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.go_to_lift_percentage.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to set cover position"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {"entity_id": entity_id, "position": 47},
                blocking=True,
            )

        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.go_to_lift_percentage.id
        )

    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(
            HomeAssistantError, match=r"Failed to set cover tilt position"
        ):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_TILT_POSITION,
                {"entity_id": entity_id, "tilt_position": 42},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id
        )

    # stop from UI
    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.stop.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to stop cover"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_STOP_COVER,
                {"entity_id": entity_id},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.stop.id
        )

    # stop from UI
    with patch(
        "zigpy.zcl.Cluster.request",
        return_value=Default_Response(
            command_id=closures.WindowCovering.ServerCommandDefs.stop.id,
            status=zcl_f.Status.UNSUP_CLUSTER_COMMAND,
        ),
    ):
        with pytest.raises(HomeAssistantError, match=r"Failed to stop cover"):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_STOP_COVER_TILT,
                {"entity_id": entity_id},
                blocking=True,
            )
        assert cluster.request.call_count == 1
        assert (
            cluster.request.call_args[0][1]
            == closures.WindowCovering.ServerCommandDefs.stop.id
        )