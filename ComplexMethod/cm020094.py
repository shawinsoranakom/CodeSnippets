async def test_button_invalid(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    knx: KNXTestKit,
    conf_type: str,
    conf_value: str,
    error_msg: str,
) -> None:
    """Test KNX button with configured payload that can't be encoded."""
    with caplog.at_level(logging.ERROR):
        await knx.setup_integration(
            {
                ButtonSchema.PLATFORM: {
                    CONF_NAME: "test",
                    KNX_ADDRESS: "1/2/3",
                    ButtonSchema.CONF_VALUE: conf_value,
                    CONF_TYPE: conf_type,
                }
            }
        )
        assert len(caplog.messages) == 2
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert f"Invalid config for 'knx': {error_msg}" in record.message
        record = caplog.records[1]
        assert record.levelname == "ERROR"
        assert "Setup failed for 'knx': Invalid config." in record.message
    assert hass.states.get("button.test") is None
    assert hass.data.get(KNX_MODULE_KEY) is None