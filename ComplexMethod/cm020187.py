async def test_entity_created_and_removed(
    caplog: pytest.LogCaptureFixture,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    storage_setup,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test tag entity created and removed."""
    caplog.at_level(logging.DEBUG)
    assert await storage_setup()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/create",
            "tag_id": "1234567890",
            "name": "Kitchen tag",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    item = resp["result"]

    assert item["id"] == "1234567890"
    assert item["name"] == "Kitchen tag"

    await hass.async_block_till_done()
    er_entity = entity_registry.async_get("tag.kitchen_tag")
    assert er_entity.name == "Kitchen tag"

    entity = hass.states.get("tag.kitchen_tag")
    assert entity
    assert entity.state == STATE_UNKNOWN
    entity_id = entity.entity_id
    assert entity_registry.async_get(entity_id)

    now = dt_util.utcnow()
    freezer.move_to(now)
    await async_scan_tag(hass, "1234567890", TEST_DEVICE_ID)

    entity = hass.states.get("tag.kitchen_tag")
    assert entity
    assert entity.state == now.isoformat(timespec="milliseconds")

    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/delete",
            "tag_id": "1234567890",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    entity = hass.states.get("tag.kitchen_tag")
    assert not entity
    assert not entity_registry.async_get(entity_id)