async def test_async_get_platforms_concurrent_loads(hass: HomeAssistant) -> None:
    """Verify async_get_platforms waits if the first load if called again.

    Case is for when when a second load is called
    and the first is still in progress.
    """
    integration = await loader.async_get_integration(
        hass, "test_package_loaded_executor"
    )
    assert integration.pkg_path == "custom_components.test_package_loaded_executor"
    assert integration.import_executor is True
    assert integration.config_flow is True

    assert "test_package_loaded_executor" not in hass.config.components
    assert "test_package_loaded_executor.config_flow" not in hass.config.components
    await integration.async_get_component()

    button_module_name = f"{integration.pkg_path}.button"
    button_module_mock = MagicMock()

    imports = []
    start_event = threading.Event()
    import_event = asyncio.Event()

    def import_module(name: str) -> Any:
        hass.loop.call_soon_threadsafe(import_event.set)
        imports.append(name)
        start_event.wait()
        if name == button_module_name:
            return button_module_mock
        raise ImportError

    modules_without_button = {
        k: v
        for k, v in sys.modules.items()
        if k not in (button_module_name, integration.pkg_path)
    }
    with (
        patch.dict(
            "sys.modules",
            modules_without_button,
            clear=True,
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        load_task1 = asyncio.create_task(integration.async_get_platforms(["button"]))
        load_task2 = asyncio.create_task(integration.async_get_platforms(["button"]))
        await import_event.wait()  # make sure the import is started
        assert not integration._import_futures["button"].done()
        start_event.set()
        load_result1 = await load_task1
        load_result2 = await load_task2
        assert integration._import_futures is not None

    assert load_result1 == {"button": button_module_mock}
    assert load_result2 == {"button": button_module_mock}

    assert imports == [button_module_name]
    assert integration.get_platform_cached("button") is button_module_mock