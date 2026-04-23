async def test_async_get_platforms_loads_loop_if_already_in_sys_modules(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify async_get_platforms does not create an executor job.

    Case is for when the module is already in sys.modules.
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
    switch_module_name = f"{integration.pkg_path}.switch"
    light_module_name = f"{integration.pkg_path}.light"
    button_module_mock = MagicMock()
    switch_module_mock = MagicMock()
    light_module_mock = MagicMock()

    def import_module(name: str) -> Any:
        if name == button_module_name:
            return button_module_mock
        if name == switch_module_name:
            return switch_module_mock
        if name == light_module_name:
            return light_module_mock
        raise ImportError

    modules_without_button = {
        k: v for k, v in sys.modules.items() if k != button_module_name
    }
    with (
        patch.dict(
            "sys.modules",
            modules_without_button,
            clear=True,
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        module = (await integration.async_get_platforms(["button"]))["button"]

    # The button module is missing so we should load
    # in the executor
    assert "executor=['button']" in caplog.text
    assert "loop=[]" in caplog.text
    assert module is button_module_mock
    caplog.clear()

    with (
        patch.dict(
            "sys.modules",
            {
                **modules_without_button,
                button_module_name: button_module_mock,
            },
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        module = (await integration.async_get_platforms(["button"]))["button"]

    # Everything is cached so there should be no logging
    assert "loop=" not in caplog.text
    assert "executor=" not in caplog.text
    assert module is button_module_mock
    caplog.clear()

    modules_without_switch = {
        k: v for k, v in sys.modules.items() if k not in switch_module_name
    }
    with (
        patch.dict(
            "sys.modules",
            {**modules_without_switch, light_module_name: light_module_mock},
            clear=True,
        ),
        patch("homeassistant.loader.importlib.import_module", import_module),
    ):
        modules = await integration.async_get_platforms(["button", "switch", "light"])

    # The button module is already in the cache so nothing happens
    # The switch module is loaded in the executor since its not in the cache
    # The light module is in memory but not in the cache so its loaded in the loop
    assert "['button']" not in caplog.text
    assert "executor=['switch']" in caplog.text
    assert "loop=['light']" in caplog.text
    assert modules == {
        "button": button_module_mock,
        "switch": switch_module_mock,
        "light": light_module_mock,
    }
    assert integration.get_platform_cached("button") is button_module_mock
    assert integration.get_platform_cached("switch") is switch_module_mock
    assert integration.get_platform_cached("light") is light_module_mock