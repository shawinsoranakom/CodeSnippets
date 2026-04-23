async def test_update_area(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
    label_registry: lr.LabelRegistry,
    freezer: FrozenDateTimeFactory,
    mock_temperature_humidity_entity: None,
) -> None:
    """Make sure that we can read areas."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)
    update_events = async_capture_events(hass, ar.EVENT_AREA_REGISTRY_UPDATED)
    floor_registry.async_create("first")
    area = area_registry.async_create("mock")
    assert area.modified_at == created_at

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)

    updated_area = area_registry.async_update(
        area.id,
        aliases={"alias_1", "alias_2"},
        floor_id="first",
        icon="mdi:garage",
        labels={"label1", "label2"},
        name="mock1",
        picture="/image/example.png",
        temperature_entity_id="sensor.mock_temperature",
        humidity_entity_id="sensor.mock_humidity",
    )

    assert updated_area != area
    assert updated_area == ar.AreaEntry(
        aliases={"alias_1", "alias_2"},
        floor_id="first",
        icon="mdi:garage",
        id=ANY,
        labels={"label1", "label2"},
        name="mock1",
        picture="/image/example.png",
        created_at=created_at,
        modified_at=modified_at,
        temperature_entity_id="sensor.mock_temperature",
        humidity_entity_id="sensor.mock_humidity",
    )
    assert len(area_registry.areas) == 1

    await hass.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0].data == {
        "action": "create",
        "area_id": area.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "area_id": area.id,
    }