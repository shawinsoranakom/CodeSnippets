async def test_ping(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    client,
    climate_danfoss_lc_13,
    climate_radio_thermostat_ct100_plus_different_endpoints,
    integration,
) -> None:
    """Test ping service."""
    device_radio_thermostat = device_registry.async_get_device(
        identifiers={
            get_device_id(
                client.driver, climate_radio_thermostat_ct100_plus_different_endpoints
            )
        }
    )
    assert device_radio_thermostat
    device_danfoss = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, climate_danfoss_lc_13)}
    )
    assert device_danfoss

    client.async_send_command.return_value = {"responded": True}

    # Test successful ping call
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PING,
        {
            ATTR_ENTITY_ID: [
                CLIMATE_DANFOSS_LC13_ENTITY,
                CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ],
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.ping"
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )
    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.ping"
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()

    # Test successful ping call with devices
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PING,
        {
            ATTR_DEVICE_ID: [
                device_radio_thermostat.id,
                device_danfoss.id,
            ],
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.ping"
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )
    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.ping"
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()

    # Test successful ping call with area
    area = area_registry.async_get_or_create("test")
    device_registry.async_update_device(device_radio_thermostat.id, area_id=area.id)
    device_registry.async_update_device(device_danfoss.id, area_id=area.id)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PING,
        {ATTR_AREA_ID: area.id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.ping"
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )
    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.ping"
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()

    # Test groups get expanded for multicast call
    assert await async_setup_component(hass, "group", {})
    await Group.async_create_group(
        hass,
        "test",
        created_by_service=False,
        entity_ids=[CLIMATE_DANFOSS_LC13_ENTITY, CLIMATE_RADIO_THERMOSTAT_ENTITY],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PING,
        {
            ATTR_ENTITY_ID: "group.test",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.ping"
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )
    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.ping"
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()

    # Test no device or entity raises error
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_PING,
            {},
            blocking=True,
        )

    client.async_send_command.reset_mock()
    client.async_send_command.side_effect = FailedZWaveCommand("test", 1, "test")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_PING,
            {
                ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            },
            blocking=True,
        )