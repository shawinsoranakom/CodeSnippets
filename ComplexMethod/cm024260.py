async def test_hassio_confirm(
    hass: HomeAssistant,
    mock_try_connection_success: MqttMockPahoClient,
    mock_finish_setup: MagicMock,
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        "mqtt",
        data=HassioServiceInfo(
            config=ADD_ON_DISCOVERY_INFO.copy(),
            name="Mosquitto Mqtt Broker",
            slug="mosquitto",
            uuid="1234",
        ),
        context={"source": config_entries.SOURCE_HASSIO},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"
    assert result["description_placeholders"] == {"addon": "Mosquitto Mqtt Broker"}

    mock_try_connection_success.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"discovery": True}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data == {
        "broker": "core-mosquitto",
        "port": 1883,
        "username": "mock-user",
        "password": "mock-pass",
        "discovery": True,
    }
    # Check we tried the connection
    assert len(mock_try_connection_success.mock_calls)
    # Check config entry got setup
    assert len(mock_finish_setup.mock_calls) == 1