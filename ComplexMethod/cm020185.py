async def test_tag_scanned(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    storage_setup,
    snapshot: SnapshotAssertion,
) -> None:
    """Test scanning tags."""
    assert await storage_setup()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert resp["result"] == [
        {"id": TEST_TAG_ID, "name": "test tag name"},
        {"id": TEST_TAG_ID_2, "name": "test tag name 2"},
    ]

    now = dt_util.utcnow()
    freezer.move_to(now)
    await async_scan_tag(hass, "new tag", "some_scanner")

    await client.send_json_auto_id({"type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 3
    assert resp["result"] == [
        {"id": TEST_TAG_ID, "name": "test tag name"},
        {"id": TEST_TAG_ID_2, "name": "test tag name 2"},
        {
            "device_id": "some_scanner",
            "id": "new tag",
            "last_scanned": now.isoformat(),
            "name": "Tag new tag",
        },
    ]

    # Trigger store
    freezer.tick(11)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass_storage[DOMAIN] == snapshot(exclude=props("last_scanned"))