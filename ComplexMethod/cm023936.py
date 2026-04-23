async def test_duplicate(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    """Test we can finish a config flow through MQTT with custom prefix."""
    discovery_info = MqttServiceInfo(
        topic="drop_connect/discovery/DROP-1_C0FFEE/255",
        payload='{"devDesc":"Hub","devType":"hub","name":"Hub DROP-1_C0FFEE"}',
        qos=0,
        retain=False,
        subscribed_topic="drop_connect/discovery/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        "drop_connect",
        context={"source": config_entries.SOURCE_MQTT},
        data=discovery_info,
    )
    assert result is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()
    assert result is not None
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Attempting configuration of the same object should abort
    result = await hass.config_entries.flow.async_init(
        "drop_connect",
        context={"source": config_entries.SOURCE_MQTT},
        data=discovery_info,
    )
    assert result is not None
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_discovery_info"