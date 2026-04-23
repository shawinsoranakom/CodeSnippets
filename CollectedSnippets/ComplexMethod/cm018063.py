async def test_async_get_component_deadlock_fallback_module_not_found(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify async_get_component fallback behavior.

    Ensure that fallback is not triggered on ModuleNotFoundError.
    """
    executor_import_integration = _get_test_integration(
        hass, "executor_import", True, import_executor=True
    )
    assert executor_import_integration.import_executor is True
    module_mock = MagicMock(__file__="__init__.py")
    import_attempts = 0

    def mock_import(module: str, *args: Any, **kwargs: Any) -> Any:
        nonlocal import_attempts
        if module == "homeassistant.components.executor_import":
            import_attempts += 1

        if import_attempts == 1:
            raise ModuleNotFoundError(
                "homeassistant.components.executor_import not found",
                name="homeassistant.components.executor_import",
            )

        return module_mock

    assert "homeassistant.components.executor_import" not in sys.modules
    assert "custom_components.executor_import" not in sys.modules
    with (
        patch("homeassistant.loader.importlib.import_module", mock_import),
        pytest.raises(
            ModuleNotFoundError, match="homeassistant.components.executor_import"
        ),
    ):
        await executor_import_integration.async_get_component()

    # We should not have tried to fall back to the event loop import
    assert "loaded_executor=False" not in caplog.text
    assert "homeassistant.components.executor_import" not in sys.modules
    assert "custom_components.executor_import" not in sys.modules
    assert import_attempts == 1