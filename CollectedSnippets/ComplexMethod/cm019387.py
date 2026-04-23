async def test_update_existing_field(
    hass: HomeAssistant,
    setup_integration: None,
    ws_get_items: Callable[[], Awaitable[dict[str, str]]],
    item_data: dict[str, Any],
    expected_item_data: dict[str, Any],
) -> None:
    """Test updating a todo item."""

    # Create new item
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {
            ATTR_ITEM: "soda",
            ATTR_DESCRIPTION: "Additional detail",
            ATTR_DUE_DATE: "2024-01-01",
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Fetch item
    items = await ws_get_items()
    assert len(items) == 1

    item = items[0]
    assert item["summary"] == "soda"
    assert item["status"] == "needs_action"

    # Perform update
    update_time = datetime(2023, 11, 18, 8, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(update_time):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.UPDATE_ITEM,
            {ATTR_ITEM: item["uid"], **item_data},
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )

    # Verify item is updated
    items = await ws_get_items()
    assert len(items) == 1
    item = items[0]
    assert item["summary"] == "soda"
    assert "uid" in item
    del item["uid"]
    assert item == expected_item_data