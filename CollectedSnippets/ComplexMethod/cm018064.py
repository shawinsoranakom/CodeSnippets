async def test_async_get_platform_deadlock_fallback(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify async_get_platform fallback to importing in the event loop on deadlock."""
    executor_import_integration = _get_test_integration(
        hass, "executor_import", True, import_executor=True
    )
    assert executor_import_integration.import_executor is True
    module_mock = MagicMock()
    import_attempts = 0

    def mock_import(module: str, *args: Any, **kwargs: Any) -> Any:
        nonlocal import_attempts
        if module == "homeassistant.components.executor_import.config_flow":
            import_attempts += 1

        if import_attempts == 1:
            # _DeadlockError inherits from RuntimeError
            raise RuntimeError(
                "Detected deadlock trying to import homeassistant.components.executor_import"
            )

        return module_mock

    assert "homeassistant.components.executor_import" not in sys.modules
    assert "custom_components.executor_import" not in sys.modules
    with patch("homeassistant.loader.importlib.import_module", mock_import):
        module = await executor_import_integration.async_get_platform("config_flow")

    assert (
        "Detected deadlock trying to import homeassistant.components.executor_import"
        in caplog.text
    )
    # We should have tried both the executor and loop
    assert "executor=['config_flow']" in caplog.text
    assert "loop=['config_flow']" in caplog.text
    assert module is module_mock