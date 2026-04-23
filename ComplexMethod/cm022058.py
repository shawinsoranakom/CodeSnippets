async def test_update_list(
    hass: HomeAssistant, sl_setup: None, snapshot: SnapshotAssertion
) -> None:
    """Test updating all list items."""
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )

    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "cheese"}}
    )
    assert_shopping_list_data(hass, snapshot)

    # Update a single attribute, other attributes shouldn't change
    await hass.data[DOMAIN].async_update_list({"complete": True})

    beer = hass.data[DOMAIN].items[0]
    assert beer["name"] == "beer"
    assert beer["complete"] is True

    cheese = hass.data[DOMAIN].items[1]
    assert cheese["name"] == "cheese"
    assert cheese["complete"] is True

    # Update multiple attributes
    await hass.data[DOMAIN].async_update_list({"name": "dupe", "complete": False})
    assert_shopping_list_data(hass, snapshot)

    beer = hass.data[DOMAIN].items[0]
    assert beer["name"] == "dupe"
    assert beer["complete"] is False

    cheese = hass.data[DOMAIN].items[1]
    assert cheese["name"] == "dupe"
    assert cheese["complete"] is False