async def test_service_call_with_ascii_qos_retain_flags(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the service call with args that can be misinterpreted.

    Empty payload message and ascii formatted qos and retain flags.
    """
    mqtt_mock = await mqtt_mock_entry()
    await hass.services.async_call(
        mqtt.DOMAIN,
        mqtt.SERVICE_PUBLISH,
        {
            mqtt.ATTR_TOPIC: "test/topic",
            mqtt.ATTR_PAYLOAD: "",
            mqtt.ATTR_QOS: "2",
            mqtt.ATTR_RETAIN: "no",
        },
        blocking=True,
    )
    assert mqtt_mock.async_publish.called
    assert mqtt_mock.async_publish.call_args[0][1] == ""
    assert mqtt_mock.async_publish.call_args[0][2] == 2
    assert not mqtt_mock.async_publish.call_args[0][3]

    mqtt_mock.reset_mock()

    # Test service call without payload
    await hass.services.async_call(
        mqtt.DOMAIN,
        mqtt.SERVICE_PUBLISH,
        {
            mqtt.ATTR_TOPIC: "test/topic",
            mqtt.ATTR_QOS: "2",
            mqtt.ATTR_RETAIN: "no",
        },
        blocking=True,
    )
    assert mqtt_mock.async_publish.called
    assert mqtt_mock.async_publish.call_args[0][1] is None
    assert mqtt_mock.async_publish.call_args[0][2] == 2
    assert not mqtt_mock.async_publish.call_args[0][3]