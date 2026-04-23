async def test_send_message(
    hass: HomeAssistant,
    matrix_bot: MatrixBot,
    image_path,
    matrix_events: list[Event],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the send_message service."""

    await hass.async_start()
    assert len(matrix_events) == 0
    await matrix_bot._login()

    # Send a message without an attached image.
    data = {ATTR_MESSAGE: "Test message", ATTR_TARGET: list(TEST_JOINABLE_ROOMS)}
    await hass.services.async_call(DOMAIN, SERVICE_SEND_MESSAGE, data, blocking=True)

    for room_alias_or_id in TEST_JOINABLE_ROOMS:
        assert f"Message delivered to room '{room_alias_or_id}'" in caplog.messages

    # Send an HTML message without an attached image.
    data = {
        ATTR_MESSAGE: "Test message",
        ATTR_TARGET: list(TEST_JOINABLE_ROOMS),
        ATTR_DATA: {ATTR_FORMAT: FORMAT_HTML},
    }
    await hass.services.async_call(DOMAIN, SERVICE_SEND_MESSAGE, data, blocking=True)

    for room_alias_or_id in TEST_JOINABLE_ROOMS:
        assert f"Message delivered to room '{room_alias_or_id}'" in caplog.messages

    # Send a message with an attached image.
    data[ATTR_DATA] = {ATTR_IMAGES: [image_path.name]}
    await hass.services.async_call(DOMAIN, SERVICE_SEND_MESSAGE, data, blocking=True)

    for room_alias_or_id in TEST_JOINABLE_ROOMS:
        assert f"Message delivered to room '{room_alias_or_id}'" in caplog.messages

    # Send a message to a thread.
    data = {
        ATTR_MESSAGE: "Test message",
        ATTR_TARGET: list(TEST_JOINABLE_ROOMS),
        ATTR_DATA: {ATTR_THREAD_ID: "thread_id"},
    }
    await hass.services.async_call(DOMAIN, SERVICE_SEND_MESSAGE, data, blocking=True)

    for room_alias_or_id in TEST_JOINABLE_ROOMS:
        assert f"Message delivered to room '{room_alias_or_id}'" in caplog.messages