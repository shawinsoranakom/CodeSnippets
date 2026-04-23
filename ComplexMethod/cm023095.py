async def test_server_logging(
    hass: HomeAssistant, client: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test automatic server logging functionality."""

    def _reset_mocks():
        client.async_send_command.reset_mock()
        client.enable_server_logging.reset_mock()
        client.disable_server_logging.reset_mock()

    # Set server logging to disabled
    client.server_logging_enabled = False

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Setup logger and set log level to debug to trigger event listener
    assert await async_setup_component(hass, "logger", {"logger": {}})
    assert logging.getLogger("zwave_js_server").getEffectiveLevel() == logging.DEBUG
    client.async_send_command.reset_mock()
    async with async_call_logger_set_level(
        "zwave_js_server", "DEBUG", hass=hass, caplog=caplog
    ):
        assert logging.getLogger("zwave_js_server").getEffectiveLevel() == logging.DEBUG

        # Validate that the server logging was enabled
        assert len(client.async_send_command.call_args_list) == 1
        assert client.async_send_command.call_args[0][0] == {
            "command": "driver.update_log_config",
            "config": {"level": "debug"},
        }
        assert client.enable_server_logging.called
        assert not client.disable_server_logging.called

        _reset_mocks()

        # Emulate server by setting log level to debug
        event = Event(
            type="log config updated",
            data={
                "source": "driver",
                "event": "log config updated",
                "config": {
                    "enabled": False,
                    "level": "debug",
                    "logToFile": True,
                    "filename": "test",
                    "forceConsole": True,
                },
            },
        )
        client.driver.receive_event(event)

        # "Enable" server logging and unload the entry
        client.server_logging_enabled = True
        await hass.config_entries.async_unload(entry.entry_id)

        # Validate that the server logging was disabled
        assert len(client.async_send_command.call_args_list) == 1
        assert client.async_send_command.call_args[0][0] == {
            "command": "driver.update_log_config",
            "config": {"level": "info"},
        }
        assert not client.enable_server_logging.called
        assert client.disable_server_logging.called

        _reset_mocks()

        # Validate that the server logging doesn't get enabled because HA thinks it already
        # is enabled
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert len(client.async_send_command.call_args_list) == 2
        assert "driver.update_log_config" not in {
            call[0][0]["command"] for call in client.async_send_command.call_args_list
        }
        assert not client.enable_server_logging.called
        assert not client.disable_server_logging.called

        _reset_mocks()

        # "Disable" server logging and unload the entry
        client.server_logging_enabled = False
        await hass.config_entries.async_unload(entry.entry_id)

        # Validate that the server logging was not disabled because HA thinks it is already
        # is disabled
        assert len(client.async_send_command.call_args_list) == 0
        assert not client.enable_server_logging.called
        assert not client.disable_server_logging.called