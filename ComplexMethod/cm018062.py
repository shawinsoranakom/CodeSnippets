async def test_async_get_component_concurrent_loads(hass: HomeAssistant) -> None:
    """Verify async_get_component waits if the first load if called again when still in progress."""
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
    imports = []
    start_event = threading.Event()
    import_event = asyncio.Event()

    def import_module(name: str) -> Any:
        hass.loop.call_soon_threadsafe(import_event.set)
        imports.append(name)
        start_event.wait()
        if name == integration.pkg_path:
            return module_mock
        if name == config_flow_module_name:
            return config_flow_module_mock
        raise ImportError

    modules_without_integration = {
        k: v
        for k, v in sys.modules.items()
        if k not in (config_flow_module_name, integration.pkg_path)
    }
    with (
        patch.dict(
            "sys.modules",
            {**modules_without_integration},
            clear=True,
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        load_task1 = asyncio.create_task(integration.async_get_component())
        load_task2 = asyncio.create_task(integration.async_get_component())
        await import_event.wait()  # make sure the import is started
        assert not integration._component_future.done()
        start_event.set()
        comp1 = await load_task1
        comp2 = await load_task2
        assert integration._component_future is None

    assert comp1 is module_mock
    assert comp2 is module_mock

    assert integration.pkg_path in imports
    assert config_flow_module_name in imports