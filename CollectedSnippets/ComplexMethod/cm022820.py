async def test_update_item(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    dav_client: Mock,
    calendar: Mock,
    update_data: dict[str, Any],
    expected_ics: list[str],
    expected_state: str,
    expected_item: dict[str, Any],
) -> None:
    """Test updating an item on the list."""

    item = Todo(dav_client, None, TODO_ALL_FIELDS, calendar, "2")
    calendar.search = MagicMock(return_value=[item])

    await hass.config_entries.async_setup(config_entry.entry_id)

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"

    calendar.todo_by_uid = MagicMock(return_value=item)

    dav_client.put.return_value.status = 204

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {
            ATTR_ITEM: "Cheese",
            **update_data,
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    assert dav_client.put.call_args
    ics = dav_client.put.call_args.args[1]
    assert compact_ics(ics) == expected_ics

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == expected_state

    result = await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.GET_ITEMS,
        {},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
        return_response=True,
    )
    assert result == {TEST_ENTITY: {"items": [expected_item]}}