async def test_deprecated_api_update(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    sl_setup: None,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the API."""

    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )
    assert_shopping_list_data(hass, snapshot)

    beer_id = hass.data["shopping_list"].items[0]["id"]
    wine_id = hass.data["shopping_list"].items[1]["id"]

    client = await hass_client()
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)
    resp = await client.post(
        f"/api/shopping_list/item/{beer_id}", json={"name": "soda"}
    )
    assert_shopping_list_data(hass, snapshot)

    assert resp.status == HTTPStatus.OK
    assert len(events) == 1
    data = await resp.json()
    assert data == {"id": beer_id, "name": "soda", "complete": False}

    resp = await client.post(
        f"/api/shopping_list/item/{wine_id}", json={"complete": True}
    )
    assert_shopping_list_data(hass, snapshot)

    assert resp.status == HTTPStatus.OK
    assert len(events) == 2
    data = await resp.json()
    assert data == {"id": wine_id, "name": "wine", "complete": True}

    beer, wine = hass.data["shopping_list"].items
    assert beer == {"id": beer_id, "name": "soda", "complete": False}
    assert wine == {"id": wine_id, "name": "wine", "complete": True}