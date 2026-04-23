async def test_sort_list_service(
    hass: HomeAssistant, sl_setup: None, snapshot: SnapshotAssertion
) -> None:
    """Test sort_all service."""

    for name in ("zzz", "ddd", "aaa"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_ITEM,
            {ATTR_NAME: name},
            blocking=True,
        )
    assert_shopping_list_data(hass, snapshot)

    # sort ascending
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SORT,
        {ATTR_REVERSE: False},
        blocking=True,
    )
    assert_shopping_list_data(hass, snapshot)

    assert hass.data[DOMAIN].items[0][ATTR_NAME] == "aaa"
    assert hass.data[DOMAIN].items[1][ATTR_NAME] == "ddd"
    assert hass.data[DOMAIN].items[2][ATTR_NAME] == "zzz"
    assert len(events) == 1

    # sort descending
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SORT,
        {ATTR_REVERSE: True},
        blocking=True,
    )
    assert_shopping_list_data(hass, snapshot)

    assert hass.data[DOMAIN].items[0][ATTR_NAME] == "zzz"
    assert hass.data[DOMAIN].items[1][ATTR_NAME] == "ddd"
    assert hass.data[DOMAIN].items[2][ATTR_NAME] == "aaa"
    assert len(events) == 2