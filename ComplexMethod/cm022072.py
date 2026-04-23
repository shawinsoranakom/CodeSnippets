async def test_move_item(
    hass: HomeAssistant,
    sl_setup: None,
    ws_get_items: WsGetItemsType,
    ws_move_item: WsMoveItemType,
    src_idx: int,
    dst_idx: int | None,
    expected_items: list[str],
) -> None:
    """Test moving a todo item within the list."""

    for i in range(1, 5):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.ADD_ITEM,
            {
                ATTR_ITEM: f"item {i}",
            },
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )

    items = await ws_get_items()
    assert len(items) == 4
    uids = [item["uid"] for item in items]
    summaries = [item["summary"] for item in items]
    assert summaries == ["item 1", "item 2", "item 3", "item 4"]

    # Prepare items for moving
    previous_uid: str | None = None
    if dst_idx is not None:
        previous_uid = uids[dst_idx]

    resp = await ws_move_item(uids[src_idx], previous_uid)
    assert resp.get("success")

    items = await ws_get_items()
    assert len(items) == 4
    summaries = [item["summary"] for item in items]
    assert summaries == expected_items