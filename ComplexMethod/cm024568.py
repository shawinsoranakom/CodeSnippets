async def test_mqtt_discovery_flow(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test MQTT discovery configuration flow."""
    payload = await async_load_fixture(hass, "mqtt-discovery-deviceinfo.json", DOMAIN)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_MQTT},
        data=MqttServiceInfo(
            topic="fully/deviceInfo/e1c9bb1-df31b345",
            payload=payload,
            qos=0,
            retain=False,
            subscribed_topic="fully/deviceInfo/+",
            timestamp=None,
        ),
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "discovery_confirm"

    confirmResult = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "test-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    assert confirmResult
    assert confirmResult.get("type") is FlowResultType.CREATE_ENTRY
    assert confirmResult.get("title") == "Test device"
    assert confirmResult.get("data") == {
        CONF_HOST: "192.168.1.234",
        CONF_PASSWORD: "test-password",
        CONF_MAC: "aa:bb:cc:dd:ee:ff",
        CONF_SSL: False,
        CONF_VERIFY_SSL: False,
    }
    assert "result" in confirmResult
    assert confirmResult["result"].unique_id == "12345"

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1