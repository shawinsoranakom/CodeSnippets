async def test_cover(
    hass: HomeAssistant,
    setup_zha: Callable[..., Coroutine[None]],
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test ZHA cover platform."""

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
        WCAttrs.current_position_lift_percentage.name: 0,  # Zigbee open %
        WCAttrs.current_position_tilt_percentage.name: 100,  # Zigbee closed %
        WCAttrs.window_covering_type.name: WCT.Tilt_blind_tilt_and_lift,
        WCAttrs.config_status.name: WCCS(~WCCS.Open_up_commands_reversed),
    }
    update_attribute_cache(cluster)

    gateway.get_or_create_device(zigpy_device)
    await gateway.async_device_initialized(zigpy_device)
    await hass.async_block_till_done(wait_background_tasks=True)

    zha_device_proxy: ZHADeviceProxy = gateway_proxy.get_device_proxy(zigpy_device.ieee)
    entity_id = find_entity_id(Platform.COVER, zha_device_proxy, hass)
    assert entity_id is not None

    assert (
        not zha_device_proxy.device.endpoints[1]
        .all_cluster_handlers[f"1:0x{cluster.cluster_id:04x}"]
        .inverted
    )
    assert cluster.read_attributes.call_count == 3
    assert (
        WCAttrs.current_position_lift_percentage.name
        in cluster.read_attributes.call_args[0][0]
    )
    assert (
        WCAttrs.current_position_tilt_percentage.name
        in cluster.read_attributes.call_args[0][0]
    )

    await async_update_entity(hass, entity_id)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100  # HA open %
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0  # HA closed %

    # test that the state has changed from open to closed
    await send_attributes_report(
        hass, cluster, {WCAttrs.current_position_lift_percentage.id: 100}
    )
    assert hass.states.get(entity_id).state == CoverState.CLOSED

    # test that it opens
    await send_attributes_report(
        hass, cluster, {WCAttrs.current_position_lift_percentage.id: 0}
    )
    assert hass.states.get(entity_id).state == CoverState.OPEN

    # test that the state remains after tilting to 0% (open)
    await send_attributes_report(
        hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 0}
    )
    assert hass.states.get(entity_id).state == CoverState.OPEN

    # test that the state remains after tilting to 100% (closed)
    await send_attributes_report(
        hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 100}
    )
    assert hass.states.get(entity_id).state == CoverState.OPEN

    # close lift from UI
    with patch("zigpy.zcl.Cluster.request", return_value=[0x1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_CLOSE_COVER, {"entity_id": entity_id}, blocking=True
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x01
        assert cluster.request.call_args[0][2].command.name == WCCmds.down_close.name
        assert cluster.request.call_args[1]["expect_reply"] is True

        assert hass.states.get(entity_id).state == CoverState.CLOSING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_lift_percentage.id: 100}
        )

        assert hass.states.get(entity_id).state == CoverState.CLOSED

    # close tilt from UI, needs re-opening first
    await send_attributes_report(
        hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 0}
    )
    assert (
        hass.states.get(entity_id).state == CoverState.CLOSED
    )  # CLOSED lift state currently takes precedence over OPEN tilt
    with patch("zigpy.zcl.Cluster.request", return_value=[0x1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER_TILT,
            {"entity_id": entity_id},
            blocking=True,
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x08
        assert (
            cluster.request.call_args[0][2].command.name
            == WCCmds.go_to_tilt_percentage.name
        )
        assert cluster.request.call_args[0][3] == 100
        assert cluster.request.call_args[1]["expect_reply"] is True

        assert hass.states.get(entity_id).state == CoverState.CLOSING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 100}
        )

        assert hass.states.get(entity_id).state == CoverState.CLOSED

    # open lift from UI
    with patch("zigpy.zcl.Cluster.request", return_value=[0x0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_OPEN_COVER, {"entity_id": entity_id}, blocking=True
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x00
        assert cluster.request.call_args[0][2].command.name == WCCmds.up_open.name
        assert cluster.request.call_args[1]["expect_reply"] is True

        assert hass.states.get(entity_id).state == CoverState.OPENING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_lift_percentage.id: 0}
        )

        assert hass.states.get(entity_id).state == CoverState.OPEN

    # open tilt from UI
    with patch("zigpy.zcl.Cluster.request", return_value=[0x0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER_TILT,
            {"entity_id": entity_id},
            blocking=True,
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x08
        assert (
            cluster.request.call_args[0][2].command.name
            == WCCmds.go_to_tilt_percentage.name
        )
        assert cluster.request.call_args[0][3] == 0
        assert cluster.request.call_args[1]["expect_reply"] is True

        assert hass.states.get(entity_id).state == CoverState.OPENING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 0}
        )

        assert hass.states.get(entity_id).state == CoverState.OPEN

    # set lift position from UI
    with patch("zigpy.zcl.Cluster.request", return_value=[0x5, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {"entity_id": entity_id, "position": 47},
            blocking=True,
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x05
        assert (
            cluster.request.call_args[0][2].command.name
            == WCCmds.go_to_lift_percentage.name
        )
        assert cluster.request.call_args[0][3] == 53
        assert cluster.request.call_args[1]["expect_reply"] is True

        assert hass.states.get(entity_id).state == CoverState.CLOSING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_lift_percentage.id: 35}
        )

        assert hass.states.get(entity_id).state == CoverState.CLOSING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_lift_percentage.id: 53}
        )

        assert hass.states.get(entity_id).state == CoverState.OPEN

    # set tilt position from UI
    with patch("zigpy.zcl.Cluster.request", return_value=[0x5, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_TILT_POSITION,
            {"entity_id": entity_id, ATTR_TILT_POSITION: 47},
            blocking=True,
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x08
        assert (
            cluster.request.call_args[0][2].command.name
            == WCCmds.go_to_tilt_percentage.name
        )
        assert cluster.request.call_args[0][3] == 53
        assert cluster.request.call_args[1]["expect_reply"] is True

        assert hass.states.get(entity_id).state == CoverState.CLOSING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 35}
        )

        assert hass.states.get(entity_id).state == CoverState.CLOSING

        await send_attributes_report(
            hass, cluster, {WCAttrs.current_position_tilt_percentage.id: 53}
        )

        assert hass.states.get(entity_id).state == CoverState.OPEN

    # stop from UI
    with patch("zigpy.zcl.Cluster.request", return_value=[0x2, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {"entity_id": entity_id}, blocking=True
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x02
        assert cluster.request.call_args[0][2].command.name == WCCmds.stop.name
        assert cluster.request.call_args[1]["expect_reply"] is True

    with patch("zigpy.zcl.Cluster.request", return_value=[0x2, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER_TILT,
            {"entity_id": entity_id},
            blocking=True,
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0x02
        assert cluster.request.call_args[0][2].command.name == WCCmds.stop.name
        assert cluster.request.call_args[1]["expect_reply"] is True