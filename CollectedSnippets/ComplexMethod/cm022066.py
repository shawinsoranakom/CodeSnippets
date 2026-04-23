async def test_complete_item_intent(hass: HomeAssistant, sl_setup) -> None:
    """Test complete item."""
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "soda"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )

    response = await intent.async_handle(
        hass, "test", "HassShoppingListCompleteItem", {"item": {"value": "beer"}}
    )

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    completed_items = response.speech_slots.get("completed_items")
    assert len(completed_items) == 2
    assert completed_items[0]["name"] == "beer"
    assert hass.data["shopping_list"].items[1]["complete"]
    assert hass.data["shopping_list"].items[2]["complete"]

    # Complete again
    response = await intent.async_handle(
        hass, "test", "HassShoppingListCompleteItem", {"item": {"value": "beer"}}
    )

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech_slots.get("completed_items") == []
    assert hass.data["shopping_list"].items[1]["complete"]
    assert hass.data["shopping_list"].items[2]["complete"]