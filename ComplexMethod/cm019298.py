async def test_notify_entity_group(
    hass: HomeAssistant, mock_notifiers: list[MockNotifyEntity]
) -> None:
    """Test sending a message to a notify group."""
    entity_title_1, entity_title_2, entity_no_title_1, entity_no_title_2 = (
        mock_notifiers
    )
    for mock_notifier in mock_notifiers:
        assert mock_notifier.send_message_mock_calls.call_count == 0

    # test group containing 1 member with title supported

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            "group_type": "notify",
            "name": "Test Group",
            "entities": ["notify.has_title_1"],
            "hide_members": True,
        },
        title="Test Group",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_SEND_MESSAGE,
        {
            ATTR_MESSAGE: "Hello",
            ATTR_TITLE: "Test notification",
            ATTR_ENTITY_ID: "notify.test_group",
        },
        blocking=True,
    )

    assert entity_title_1.send_message_mock_calls.call_count == 1
    assert entity_title_1.send_message_mock_calls.call_args == call(
        "Hello", title="Test notification"
    )

    for mock_notifier in mock_notifiers:
        mock_notifier.send_message_mock_calls.reset_mock()

    # test group containing 1 member with title supported but no title provided

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_SEND_MESSAGE,
        {
            ATTR_MESSAGE: "Hello",
            ATTR_ENTITY_ID: "notify.test_group",
        },
        blocking=True,
    )

    assert entity_title_1.send_message_mock_calls.call_count == 1
    assert entity_title_1.send_message_mock_calls.call_args == call("Hello", title=None)

    for mock_notifier in mock_notifiers:
        mock_notifier.send_message_mock_calls.reset_mock()

    # test group containing 2 members with title supported

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            "group_type": "notify",
            "name": "Test Group 2",
            "entities": ["notify.has_title_1", "notify.has_title_2"],
            "hide_members": True,
        },
        title="Test Group 2",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_SEND_MESSAGE,
        {
            ATTR_MESSAGE: "Hello",
            ATTR_TITLE: "Test notification",
            ATTR_ENTITY_ID: "notify.test_group_2",
        },
        blocking=True,
    )

    assert entity_title_1.send_message_mock_calls.call_count == 1
    assert entity_title_1.send_message_mock_calls.call_args == call(
        "Hello", title="Test notification"
    )
    assert entity_title_2.send_message_mock_calls.call_count == 1
    assert entity_title_2.send_message_mock_calls.call_args == call(
        "Hello", title="Test notification"
    )

    for mock_notifier in mock_notifiers:
        mock_notifier.send_message_mock_calls.reset_mock()

    # test group containing 2 members: 1 title supported and 1 not supported
    # title is not supported since not all members support it

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            "group_type": "notify",
            "name": "Test Group",
            "entities": ["notify.has_title_1", "notify.no_title_1"],
            "hide_members": True,
        },
        title="Test Group 3",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_SEND_MESSAGE,
        {
            ATTR_MESSAGE: "Hello",
            ATTR_TITLE: "Test notification",
            ATTR_ENTITY_ID: "notify.test_group_3",
        },
        blocking=True,
    )

    assert entity_title_1.send_message_mock_calls.call_count == 1
    assert entity_title_1.send_message_mock_calls.call_args == call("Hello", title=None)
    assert entity_no_title_1.send_message_mock_calls.call_count == 1
    assert entity_no_title_1.send_message_mock_calls.call_args == call(
        "Hello", title=None
    )

    for mock_notifier in mock_notifiers:
        mock_notifier.send_message_mock_calls.reset_mock()

    # test group containing 2 members: both not supporting title

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            "group_type": "notify",
            "name": "Test Group",
            "entities": ["notify.no_title_1", "notify.no_title_2"],
            "hide_members": True,
        },
        title="Test Group 4",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_SEND_MESSAGE,
        {
            ATTR_MESSAGE: "Hello",
            ATTR_TITLE: "Test notification",
            ATTR_ENTITY_ID: "notify.test_group_4",
        },
        blocking=True,
    )

    assert entity_no_title_1.send_message_mock_calls.call_count == 1
    assert entity_no_title_1.send_message_mock_calls.call_args == call(
        "Hello", title=None
    )
    assert entity_no_title_2.send_message_mock_calls.call_count == 1
    assert entity_no_title_2.send_message_mock_calls.call_args == call(
        "Hello", title=None
    )