async def test_update_floor(
    hass: HomeAssistant,
    floor_registry: fr.FloorRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Make sure that we can update floors."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)

    update_events = async_capture_events(hass, fr.EVENT_FLOOR_REGISTRY_UPDATED)
    floor = floor_registry.async_create("First floor")

    assert floor == fr.FloorEntry(
        floor_id="first_floor",
        name="First floor",
        icon=None,
        aliases=set(),
        level=None,
        created_at=created_at,
        modified_at=created_at,
    )
    assert len(floor_registry.floors) == 1

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)

    updated_floor = floor_registry.async_update(
        floor.floor_id,
        name="Second floor",
        icon="mdi:home-floor-2",
        aliases={"ground", "downstairs"},
        level=2,
    )

    assert updated_floor != floor
    assert updated_floor == fr.FloorEntry(
        floor_id="first_floor",
        name="Second floor",
        icon="mdi:home-floor-2",
        aliases={"ground", "downstairs"},
        level=2,
        created_at=created_at,
        modified_at=modified_at,
    )

    assert len(floor_registry.floors) == 1

    await hass.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0].data == {
        "action": "create",
        "floor_id": floor.floor_id,
    }
    assert update_events[1].data == {
        "action": "update",
        "floor_id": floor.floor_id,
    }