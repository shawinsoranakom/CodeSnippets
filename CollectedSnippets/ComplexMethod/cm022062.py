async def test_deprecated_api_create(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    sl_setup: None,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the API."""

    client = await hass_client()
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)
    resp = await client.post("/api/shopping_list/item", json={"name": "soda"})
    assert_shopping_list_data(hass, snapshot)

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["name"] == "soda"
    assert data["complete"] is False
    assert len(events) == 1

    items = hass.data["shopping_list"].items
    assert len(items) == 1
    assert items[0]["name"] == "soda"
    assert items[0]["complete"] is False