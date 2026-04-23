async def test_setting_level(hass: HomeAssistant) -> None:
    """Test we set log levels."""
    mocks = defaultdict(Mock)

    with patch("logging.getLogger", mocks.__getitem__):
        assert await async_setup_component(
            hass,
            "logger",
            {
                "logger": {
                    "default": "warning",
                    "logs": {
                        "test": "info",
                        "test.child": "debug",
                        "test.child.child": "warning",
                    },
                }
            },
        )
        await hass.async_block_till_done()

    assert len(mocks) == 5

    assert len(mocks[""].orig_setLevel.mock_calls) == 1
    assert mocks[""].orig_setLevel.mock_calls[0][1][0] == LOGSEVERITY["WARNING"]

    assert len(mocks["test"].orig_setLevel.mock_calls) == 1
    assert mocks["test"].orig_setLevel.mock_calls[0][1][0] == LOGSEVERITY["INFO"]

    assert len(mocks["test.child"].orig_setLevel.mock_calls) == 1
    assert mocks["test.child"].orig_setLevel.mock_calls[0][1][0] == LOGSEVERITY["DEBUG"]

    assert len(mocks["test.child.child"].orig_setLevel.mock_calls) == 1
    assert (
        mocks["test.child.child"].orig_setLevel.mock_calls[0][1][0]
        == LOGSEVERITY["WARNING"]
    )

    assert len(mocks["homeassistant.components.logger"].orig_setLevel.mock_calls) == 0

    # Test set default level
    with patch("logging.getLogger", mocks.__getitem__):
        await hass.services.async_call(
            "logger", "set_default_level", {"level": "fatal"}, blocking=True
        )
    assert len(mocks[""].orig_setLevel.mock_calls) == 2
    assert mocks[""].orig_setLevel.mock_calls[1][1][0] == LOGSEVERITY["FATAL"]

    # Test update other loggers
    with patch("logging.getLogger", mocks.__getitem__):
        await hass.services.async_call(
            "logger",
            "set_level",
            {"test.child": "info", "new_logger": "notset"},
            blocking=True,
        )
    assert len(mocks) == 6

    assert len(mocks["test.child"].orig_setLevel.mock_calls) == 2
    assert mocks["test.child"].orig_setLevel.mock_calls[1][1][0] == LOGSEVERITY["INFO"]

    assert len(mocks["new_logger"].orig_setLevel.mock_calls) == 1
    assert (
        mocks["new_logger"].orig_setLevel.mock_calls[0][1][0] == LOGSEVERITY["NOTSET"]
    )