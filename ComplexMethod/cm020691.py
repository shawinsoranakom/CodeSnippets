async def test_on_with_off_color(
    hass: HomeAssistant,
    setup_zha: Callable[..., Coroutine[None]],
    zigpy_device_mock: Callable[..., Device],
) -> None:
    """Test turning on the light and sending color commands before on/level commands for supporting lights."""

    await setup_zha()
    gateway = get_zha_gateway(hass)
    gateway_proxy: ZHAGatewayProxy = get_zha_gateway_proxy(hass)

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [
                    general.OnOff.cluster_id,
                    general.LevelControl.cluster_id,
                    lighting.Color.cluster_id,
                    general.Groups.cluster_id,
                    general.Identify.cluster_id,
                ],
                SIG_EP_OUTPUT: [],
                SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT,
                SIG_EP_PROFILE: zha.PROFILE_ID,
            }
        },
        nwk=0xB79D,
    )

    dev1_cluster_color = zigpy_device.endpoints[1].light_color

    dev1_cluster_color.PLUGGED_ATTR_READS = {
        "color_capabilities": lighting.Color.ColorCapabilities.Color_temperature
        | lighting.Color.ColorCapabilities.XY_attributes
    }

    gateway.get_or_create_device(zigpy_device)
    await gateway.async_device_initialized(zigpy_device)
    await hass.async_block_till_done(wait_background_tasks=True)

    zha_device_proxy: ZHADeviceProxy = gateway_proxy.get_device_proxy(zigpy_device.ieee)
    entity_id = find_entity_id(Platform.LIGHT, zha_device_proxy, hass)
    assert entity_id is not None

    device_1_entity_id = find_entity_id(Platform.LIGHT, zha_device_proxy, hass)
    dev1_cluster_on_off = zigpy_device.endpoints[1].on_off
    dev1_cluster_level = zigpy_device.endpoints[1].level

    # Execute_if_off will override the "enhanced turn on from an off-state" config option that's enabled here
    dev1_cluster_color.PLUGGED_ATTR_READS = {
        "options": lighting.Color.Options.Execute_if_off
    }
    update_attribute_cache(dev1_cluster_color)

    # turn on via UI
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            "entity_id": device_1_entity_id,
            "color_temp_kelvin": 4255,
        },
        blocking=True,
    )

    assert dev1_cluster_on_off.request.call_count == 1
    assert dev1_cluster_on_off.request.await_count == 1
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 0
    assert dev1_cluster_level.request.await_count == 0

    assert dev1_cluster_on_off.request.call_args_list[0] == call(
        False,
        dev1_cluster_on_off.commands_by_name["on"].id,
        dev1_cluster_on_off.commands_by_name["on"].schema,
        expect_reply=True,
        manufacturer=None,
    )
    assert dev1_cluster_color.request.call_args == call(
        False,
        dev1_cluster_color.commands_by_name["move_to_color_temp"].id,
        dev1_cluster_color.commands_by_name["move_to_color_temp"].schema,
        color_temp_mireds=235,
        transition_time=0,
        expect_reply=True,
        manufacturer=None,
    )

    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes["color_temp_kelvin"] == 4255
    assert light1_state.attributes["color_mode"] == ColorMode.COLOR_TEMP

    # now let's turn off the Execute_if_off option and see if the old behavior is restored
    dev1_cluster_color.PLUGGED_ATTR_READS = {"options": 0}
    update_attribute_cache(dev1_cluster_color)

    # turn off via UI, so the old "enhanced turn on from an off-state" behavior can do something
    await async_test_off_from_hass(hass, dev1_cluster_on_off, device_1_entity_id)

    # turn on via UI (with a different color temp, so the "enhanced turn on" does something)
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            "entity_id": device_1_entity_id,
            "color_temp_kelvin": 4166,
        },
        blocking=True,
    )

    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 2
    assert dev1_cluster_level.request.await_count == 2

    # first it comes on with no transition at 2 brightness
    assert dev1_cluster_level.request.call_args_list[0] == call(
        False,
        dev1_cluster_level.commands_by_name["move_to_level_with_on_off"].id,
        dev1_cluster_level.commands_by_name["move_to_level_with_on_off"].schema,
        level=2,
        transition_time=0,
        expect_reply=True,
        manufacturer=None,
    )
    assert dev1_cluster_color.request.call_args == call(
        False,
        dev1_cluster_color.commands_by_name["move_to_color_temp"].id,
        dev1_cluster_color.commands_by_name["move_to_color_temp"].schema,
        color_temp_mireds=240,
        transition_time=0,
        expect_reply=True,
        manufacturer=None,
    )
    assert dev1_cluster_level.request.call_args_list[1] == call(
        False,
        dev1_cluster_level.commands_by_name["move_to_level"].id,
        dev1_cluster_level.commands_by_name["move_to_level"].schema,
        level=254,
        transition_time=0,
        expect_reply=True,
        manufacturer=None,
    )

    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes["brightness"] == 254
    assert light1_state.attributes["color_temp_kelvin"] == 4166
    assert light1_state.attributes["color_mode"] == ColorMode.COLOR_TEMP