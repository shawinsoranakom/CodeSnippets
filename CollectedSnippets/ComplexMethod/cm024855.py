async def test_create_area(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    area_registry: ar.AreaRegistry,
    mock_temperature_humidity_entity: None,
) -> None:
    """Make sure that we can create an area."""
    update_events = async_capture_events(hass, ar.EVENT_AREA_REGISTRY_UPDATED)

    # Create area with only mandatory parameters
    area = area_registry.async_create("mock")

    assert area == ar.AreaEntry(
        aliases=set(),
        floor_id=None,
        icon=None,
        id=ANY,
        labels=set(),
        name="mock",
        picture=None,
        created_at=utcnow(),
        modified_at=utcnow(),
        temperature_entity_id=None,
        humidity_entity_id=None,
    )
    assert len(area_registry.areas) == 1

    freezer.tick(timedelta(minutes=5))

    await hass.async_block_till_done()

    assert len(update_events) == 1
    assert update_events[-1].data == {
        "action": "create",
        "area_id": area.id,
    }

    # Create area with all parameters
    area2 = area_registry.async_create(
        "mock 2",
        aliases={"alias_1", "alias_2"},
        labels={"label1", "label2"},
        picture="/image/example.png",
        temperature_entity_id="sensor.mock_temperature",
        humidity_entity_id="sensor.mock_humidity",
    )

    assert area2 == ar.AreaEntry(
        aliases={"alias_1", "alias_2"},
        floor_id=None,
        icon=None,
        id=ANY,
        labels={"label1", "label2"},
        name="mock 2",
        picture="/image/example.png",
        created_at=utcnow(),
        modified_at=utcnow(),
        temperature_entity_id="sensor.mock_temperature",
        humidity_entity_id="sensor.mock_humidity",
    )
    assert len(area_registry.areas) == 2
    assert area.created_at != area2.created_at
    assert area.modified_at != area2.modified_at

    await hass.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[-1].data == {
        "action": "create",
        "area_id": area2.id,
    }