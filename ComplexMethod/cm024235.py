async def test_publish(
    hass: HomeAssistant, setup_with_birth_msg_client_mock: MqttMockPahoClient
) -> None:
    """Test the publish function."""
    publish_mock: MagicMock = setup_with_birth_msg_client_mock.publish
    await mqtt.async_publish(hass, "test-topic", "test-payload")
    await hass.async_block_till_done()
    assert publish_mock.called
    assert publish_mock.call_args[0] == (
        "test-topic",
        "test-payload",
        0,
        False,
    )
    publish_mock.reset_mock()

    await mqtt.async_publish(hass, "test-topic", "test-payload", 2, True)
    await hass.async_block_till_done()
    assert publish_mock.called
    assert publish_mock.call_args[0] == (
        "test-topic",
        "test-payload",
        2,
        True,
    )
    publish_mock.reset_mock()

    mqtt.publish(hass, "test-topic2", "test-payload2")
    await hass.async_block_till_done()
    assert publish_mock.called
    assert publish_mock.call_args[0] == (
        "test-topic2",
        "test-payload2",
        0,
        False,
    )
    publish_mock.reset_mock()

    mqtt.publish(hass, "test-topic2", "test-payload2", 2, True)
    await hass.async_block_till_done()
    assert publish_mock.called
    assert publish_mock.call_args[0] == (
        "test-topic2",
        "test-payload2",
        2,
        True,
    )
    publish_mock.reset_mock()

    # test binary pass-through
    mqtt.publish(
        hass,
        "test-topic3",
        b"\xde\xad\xbe\xef",
        0,
        False,
    )
    await hass.async_block_till_done()
    assert publish_mock.called
    assert publish_mock.call_args[0] == (
        "test-topic3",
        b"\xde\xad\xbe\xef",
        0,
        False,
    )
    publish_mock.reset_mock()

    # test null payload
    mqtt.publish(
        hass,
        "test-topic3",
        None,
        0,
        False,
    )
    await hass.async_block_till_done()
    assert publish_mock.called
    assert publish_mock.call_args[0] == (
        "test-topic3",
        None,
        0,
        False,
    )

    publish_mock.reset_mock()