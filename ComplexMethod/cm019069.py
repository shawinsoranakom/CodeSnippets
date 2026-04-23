async def test_async_step_user_success(hass: HomeAssistant) -> None:
    """Test user step success."""
    with patch("pyvera.VeraController") as vera_controller_class_mock:
        controller = MagicMock()
        controller.refresh_data = MagicMock()
        controller.serial_number = "serial_number_0"
        vera_controller_class_mock.return_value = controller

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == config_entries.SOURCE_USER

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONTROLLER: "http://127.0.0.1:123/",
                CONF_LIGHTS: "12 13",
                CONF_EXCLUDE: "14 15",
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "http://127.0.0.1:123"
        assert result["data"] == {
            CONF_CONTROLLER: "http://127.0.0.1:123",
            CONF_SOURCE: config_entries.SOURCE_USER,
            CONF_LIGHTS: [12, 13],
            CONF_EXCLUDE: [14, 15],
            CONF_LEGACY_UNIQUE_ID: False,
        }
        assert result["result"].unique_id == controller.serial_number

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries