async def test_hassio_cannot_connect(
    hass: HomeAssistant,
    mock_try_connection_time_out: MagicMock,
    mock_finish_setup: MagicMock,
) -> None:
    """Test a config flow is aborted when a connection was not successful."""
    result = await hass.config_entries.flow.async_init(
        "mqtt",
        data=HassioServiceInfo(
            config={
                "addon": "Mock Addon",
                "host": "core-mosquitto",
                "port": 1883,
                "username": "mock-user",
                "password": "mock-pass",
                "protocol": "3.1.1",  # Set by the addon's discovery, ignored by HA
                "ssl": False,  # Set by the addon's discovery, ignored by HA
            },
            name="Mock Addon",
            slug="mosquitto",
            uuid="1234",
        ),
        context={"source": config_entries.SOURCE_HASSIO},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"
    assert result["description_placeholders"] == {"addon": "Mock Addon"}

    mock_try_connection_time_out.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"discovery": True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"
    # Check we tried the connection
    assert len(mock_try_connection_time_out.mock_calls)
    # Check config entry got setup
    assert len(mock_finish_setup.mock_calls) == 0