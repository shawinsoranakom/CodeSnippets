async def test_async_get_component_loads_loop_if_already_in_sys_modules(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify async_get_component does not create an executor job if the module is already in sys.modules."""
    integration = await loader.async_get_integration(
        hass, "test_package_loaded_executor"
    )
    assert integration.pkg_path == "custom_components.test_package_loaded_executor"
    assert integration.import_executor is True
    assert integration.config_flow is True

    assert "test_package_loaded_executor" not in hass.config.components
    assert "test_package_loaded_executor.config_flow" not in hass.config.components

    config_flow_module_name = f"{integration.pkg_path}.config_flow"
    module_mock = MagicMock(__file__="__init__.py")
    config_flow_module_mock = MagicMock(__file__="config_flow.py")

    def import_module(name: str) -> Any:
        if name == integration.pkg_path:
            return module_mock
        if name == config_flow_module_name:
            return config_flow_module_mock
        raise ImportError

    modules_without_config_flow = {
        k: v for k, v in sys.modules.items() if k != config_flow_module_name
    }
    with (
        patch.dict(
            "sys.modules",
            {**modules_without_config_flow, integration.pkg_path: module_mock},
            clear=True,
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        module = await integration.async_get_component()

    # The config flow is missing so we should load
    # in the executor
    assert "loaded_executor=True" in caplog.text
    assert "loaded_executor=False" not in caplog.text
    assert module is module_mock
    caplog.clear()

    with (
        patch.dict(
            "sys.modules",
            {
                integration.pkg_path: module_mock,
                config_flow_module_name: config_flow_module_mock,
            },
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        module = await integration.async_get_component()

    # Everything is already in the integration cache
    # so it should not have to call the load
    assert "loaded_executor" not in caplog.text
    assert module is module_mock