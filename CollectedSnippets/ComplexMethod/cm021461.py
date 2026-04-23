async def test_moving_todo_item(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test for moving a To-do Item to place."""
    await setup_integration(hass, mock_config_entry)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "todo/item/move",
            "entity_id": "todo.mealie_supermarket",
            "uid": "f45430f7-3edf-45a9-a50f-73bb375090be",
            "previous_uid": "84d8fd74-8eb0-402e-84b6-71f251bfb7cc",
        }
    )
    resp = await client.receive_json()
    assert resp.get("id") == 1
    assert resp.get("success")
    assert resp.get("result") is None

    assert mock_mealie_client.update_shopping_item.call_count == 4
    calls = mock_mealie_client.update_shopping_item.mock_calls

    assert calls[0] == call(
        "84d8fd74-8eb0-402e-84b6-71f251bfb7cc",
        MutateShoppingItem(
            item_id="84d8fd74-8eb0-402e-84b6-71f251bfb7cc",
            list_id="9ce096fe-ded2-4077-877d-78ba450ab13e",
            note="",
            display=None,
            checked=False,
            position=0,
            is_food=True,
            disable_amount=None,
            quantity=1.0,
            label_id=None,
            food_id="09322430-d24c-4b1a-abb6-22b6ed3a88f5",
            unit_id="7bf539d4-fc78-48bc-b48e-c35ccccec34a",
        ),
    )

    assert calls[1] == call(
        "f45430f7-3edf-45a9-a50f-73bb375090be",
        MutateShoppingItem(
            item_id="f45430f7-3edf-45a9-a50f-73bb375090be",
            list_id="9ce096fe-ded2-4077-877d-78ba450ab13e",
            note="Apples",
            display=None,
            checked=False,
            position=1,
            quantity=2.0,
            label_id=None,
            food_id=None,
            unit_id=None,
        ),
    )

    assert calls[2] == call(
        "69913b9a-7c75-4935-abec-297cf7483f88",
        MutateShoppingItem(
            item_id="69913b9a-7c75-4935-abec-297cf7483f88",
            list_id="9ce096fe-ded2-4077-877d-78ba450ab13e",
            note="",
            display=None,
            checked=False,
            position=2,
            is_food=True,
            disable_amount=None,
            quantity=0.0,
            label_id=None,
            food_id="96801494-4e26-4148-849a-8155deb76327",
            unit_id=None,
        ),
    )