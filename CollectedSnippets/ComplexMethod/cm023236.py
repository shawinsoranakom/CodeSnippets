async def test_device_diagnostics_missing_primary_value(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client,
    multisensor_6,
    integration,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test that device diagnostics handles an entity with a missing primary value."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, multisensor_6)}
    )
    assert device

    entity_id = "sensor.multisensor_6_air_temperature"
    entry = entity_registry.async_get(entity_id)
    assert entry

    # check that the primary value for the entity exists in the diagnostics
    diagnostics_data = await get_diagnostics_for_device(
        hass, hass_client, integration, device
    )

    value = multisensor_6.values.get(get_value_id_from_unique_id(entry.unique_id))
    assert value

    diagnostics_entities = cast(list[dict[str, Any]], diagnostics_data["entities"])
    air_entity = next(x for x in diagnostics_entities if x["entity_id"] == entity_id)

    assert air_entity["value_id"] == value.value_id
    assert air_entity["primary_value"] == {
        "command_class": value.command_class,
        "command_class_name": value.command_class_name,
        "endpoint": value.endpoint,
        "property": value.property_,
        "property_name": value.property_name,
        "property_key": value.property_key,
        "property_key_name": value.property_key_name,
    }

    # make the entity's primary value go missing
    event = Event(
        type="value removed",
        data={
            "source": "node",
            "event": "value removed",
            "nodeId": multisensor_6.node_id,
            "args": {
                "commandClassName": value.command_class_name,
                "commandClass": value.command_class,
                "endpoint": value.endpoint,
                "property": value.property_,
                "prevValue": 0,
                "propertyName": value.property_name,
            },
        },
    )
    multisensor_6.receive_event(event)

    diagnostics_data = await get_diagnostics_for_device(
        hass, hass_client, integration, device
    )

    diagnostics_entities = cast(list[dict[str, Any]], diagnostics_data["entities"])
    air_entity = next(x for x in diagnostics_entities if x["entity_id"] == entity_id)

    assert air_entity["value_id"] == value.value_id
    assert air_entity["primary_value"] is None