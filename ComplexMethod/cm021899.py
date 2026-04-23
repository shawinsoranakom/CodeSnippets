async def test_dimmer_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_api: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Tests dimmer entity."""

    device_name = "Light Controller"
    entity_key = "light.light_controller_test_entity_name"
    entity_type = "dimmer"
    entity_type_override = "light"

    mock_api.lights = [
        mock_api_device(device_name=device_name, entity_type=entity_type)
    ]

    await setup_platform(hass, Platform.LIGHT)

    entity = entity_registry.entities[entity_key]
    assert entity.unique_id == ENTITY_INFO["id"]

    assert entity.capabilities == {
        "supported_color_modes": [ColorMode.BRIGHTNESS],
    }

    state = hass.states.get(entity_key)
    assert state == snapshot

    services = hass.services.async_services()

    assert SERVICE_TURN_ON in services[entity_type_override]

    await hass.services.async_call(
        entity_type_override,
        SERVICE_TURN_ON,
        {"entity_id": entity_key},
        blocking=True,
    )

    assert mock_api.lights[0].set_brightness.called

    assert SERVICE_TURN_OFF in services[entity_type_override]

    await hass.services.async_call(
        entity_type_override,
        SERVICE_TURN_OFF,
        {"entity_id": entity_key},
        blocking=True,
    )

    assert mock_api.lights[0].set_brightness.called