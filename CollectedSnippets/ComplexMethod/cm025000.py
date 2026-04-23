async def test_update_label(
    hass: HomeAssistant,
    label_registry: lr.LabelRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Make sure that we can update labels."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)
    update_events = async_capture_events(hass, lr.EVENT_LABEL_REGISTRY_UPDATED)
    label = label_registry.async_create("Mock")

    assert len(label_registry.labels) == 1
    assert label == lr.LabelEntry(
        label_id="mock",
        name="Mock",
        color=None,
        icon=None,
        description=None,
        created_at=created_at,
        modified_at=created_at,
    )

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)
    updated_label = label_registry.async_update(
        label.label_id,
        name="Updated",
        color="#FFFFFF",
        icon="mdi:update",
        description="Updated description",
    )

    assert updated_label != label
    assert updated_label == lr.LabelEntry(
        label_id="mock",
        name="Updated",
        color="#FFFFFF",
        icon="mdi:update",
        description="Updated description",
        created_at=created_at,
        modified_at=modified_at,
    )
    assert len(label_registry.labels) == 1

    await hass.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0].data == {
        "action": "create",
        "label_id": label.label_id,
    }
    assert update_events[1].data == {
        "action": "update",
        "label_id": label.label_id,
    }