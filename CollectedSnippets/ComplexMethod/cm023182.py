async def test_refresh_value(
    hass: HomeAssistant,
    client,
    climate_radio_thermostat_ct100_plus_different_endpoints,
    integration,
) -> None:
    """Test the refresh_value service."""
    # Test polling the primary value
    client.async_send_command.return_value = {"result": 2}
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.poll_value"
    assert args["nodeId"] == 26
    assert args["valueId"] == {
        "commandClass": 64,
        "endpoint": 1,
        "property": "mode",
    }

    client.async_send_command.reset_mock()

    # Test polling all watched values
    client.async_send_command.return_value = {"result": 2}
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ATTR_REFRESH_ALL_VALUES: True,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 8

    client.async_send_command.reset_mock()

    # Test polling all watched values using string for boolean
    client.async_send_command.return_value = {"result": 2}
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ATTR_REFRESH_ALL_VALUES: "true",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 8

    client.async_send_command.reset_mock()

    # Test groups get expanded
    assert await async_setup_component(hass, "group", {})
    await Group.async_create_group(
        hass,
        "test",
        created_by_service=False,
        entity_ids=[CLIMATE_RADIO_THERMOSTAT_ENTITY],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    client.async_send_command.return_value = {"result": 2}
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {
            ATTR_ENTITY_ID: "group.test",
            ATTR_REFRESH_ALL_VALUES: "true",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 8

    client.async_send_command.reset_mock()

    # Test polling against an invalid entity raises MultipleInvalid
    with pytest.raises(vol.MultipleInvalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_REFRESH_VALUE,
            {ATTR_ENTITY_ID: "sensor.fake_entity_id"},
            blocking=True,
        )