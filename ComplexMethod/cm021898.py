async def test_light_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_api: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Tests lights entity."""

    device_name = "Light Controller"
    entity_key = "light.light_controller_test_entity_name"
    entity_type = "light"

    mock_api.lights = [
        mock_api_device(device_name=device_name, entity_type=entity_type)
    ]

    await setup_platform(hass, Platform.LIGHT)

    entity = entity_registry.entities[entity_key]
    assert entity.unique_id == ENTITY_INFO["id"]

    assert entity.capabilities == {
        "supported_color_modes": [ColorMode.ONOFF],
    }

    state = hass.states.get(entity_key)
    assert state == snapshot

    services = hass.services.async_services()

    assert SERVICE_TURN_ON in services[entity_type]

    await hass.services.async_call(
        entity_type,
        SERVICE_TURN_ON,
        {"entity_id": entity_key},
        blocking=True,
    )

    assert mock_api.lights[0].turn_on.called

    assert SERVICE_TURN_OFF in services[entity_type]

    await hass.services.async_call(
        entity_type,
        SERVICE_TURN_OFF,
        {"entity_id": entity_key},
        blocking=True,
    )

    assert mock_api.lights[0].turn_off.called