async def test_entity(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    storage_setup,
) -> None:
    """Test tag entity."""
    assert await storage_setup()

    await hass_ws_client(hass)

    entity = hass.states.get("tag.test_tag_name")
    assert entity
    assert entity.state == STATE_UNKNOWN

    now = dt_util.utcnow()
    freezer.move_to(now)
    await async_scan_tag(hass, TEST_TAG_ID, TEST_DEVICE_ID)

    entity = hass.states.get("tag.test_tag_name")
    assert entity
    assert entity.state == now.isoformat(timespec="milliseconds")
    assert entity.attributes == {
        "tag_id": "test tag id",
        "last_scanned_by_device_id": "device id",
        "friendly_name": "test tag name",
    }

    entity = hass.states.get("tag.test_tag_name_2")
    assert entity
    assert entity.state == STATE_UNKNOWN