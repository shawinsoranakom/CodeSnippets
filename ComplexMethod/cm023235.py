async def test_device_diagnostics(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client,
    multisensor_6,
    integration,
    hass_client: ClientSessionGenerator,
    version_state,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the device level diagnostics data dump."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, multisensor_6)}
    )
    assert device

    # Create mock config entry for fake entity
    mock_config_entry = MockConfigEntry(domain="test_integration")
    mock_config_entry.add_to_hass(hass)

    # Add an entity entry to the device that is not part of this config entry
    entity_registry.async_get_or_create(
        "test",
        "test_integration",
        "test_unique_id",
        suggested_object_id="unrelated_entity",
        config_entry=mock_config_entry,
        device_id=device.id,
    )
    assert entity_registry.async_get("test.unrelated_entity")

    # Update a value and ensure it is reflected in the node state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": multisensor_6.node_id,
            "args": {
                "commandClassName": "Multilevel Sensor",
                "commandClass": 49,
                "endpoint": 0,
                "property": PROPERTY_ULTRAVIOLET,
                "newValue": 1,
                "prevValue": 0,
                "propertyName": PROPERTY_ULTRAVIOLET,
            },
        },
    )
    multisensor_6.receive_event(event)

    diagnostics_data = await get_diagnostics_for_device(
        hass, hass_client, integration, device
    )
    assert diagnostics_data["versionInfo"] == {
        "driverVersion": version_state["driverVersion"],
        "serverVersion": version_state["serverVersion"],
        "minSchemaVersion": 0,
        "maxSchemaVersion": 0,
    }
    # Assert that we only have the entities that were discovered for this device
    # Entities that are created outside of discovery (e.g. node status sensor and
    # ping button) as well as helper entities created from other integrations should
    # not be in dump.
    assert diagnostics_data == snapshot

    assert any(
        entity_entry.entity_id == "test.unrelated_entity"
        for entity_entry in er.async_entries_for_device(entity_registry, device.id)
    )
    # Explicitly check that the entity that is not part of this config entry is not
    # in the dump.
    diagnostics_entities = cast(list[dict[str, Any]], diagnostics_data["entities"])
    assert not any(
        entity["entity_id"] == "test.unrelated_entity"
        for entity in diagnostics_entities
    )
    assert diagnostics_data["state"] == {
        **multisensor_6.data,
        "values": {
            value_id: val.data for value_id, val in multisensor_6.values.items()
        },
        "endpoints": {
            str(idx): endpoint.data for idx, endpoint in multisensor_6.endpoints.items()
        },
    }