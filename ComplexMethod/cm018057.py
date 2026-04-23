async def test_async_get_platform_caches_failures_when_component_loaded(
    hass: HomeAssistant,
) -> None:
    """Test async_get_platform caches failures only when the component is loaded.

    Only ModuleNotFoundError is cached, ImportError is not cached.
    """
    integration = await loader.async_get_integration(hass, "hue")

    with (
        pytest.raises(ModuleNotFoundError),
        patch(
            "homeassistant.loader.importlib.import_module",
            side_effect=ModuleNotFoundError("Boom"),
        ),
    ):
        assert integration.get_component() == hue

    with (
        pytest.raises(ModuleNotFoundError),
        patch(
            "homeassistant.loader.importlib.import_module",
            side_effect=ModuleNotFoundError("Boom"),
        ),
    ):
        assert await integration.async_get_platform("light") == hue_light

    # Hue is not loaded so we should still hit the import_module path
    with (
        pytest.raises(ModuleNotFoundError),
        patch(
            "homeassistant.loader.importlib.import_module",
            side_effect=ModuleNotFoundError("Boom"),
        ),
    ):
        assert await integration.async_get_platform("light") == hue_light

    assert integration.get_component() == hue

    # Hue is loaded so we should cache the import_module failure now
    with (
        pytest.raises(ModuleNotFoundError),
        patch(
            "homeassistant.loader.importlib.import_module",
            side_effect=ModuleNotFoundError("Boom"),
        ),
    ):
        assert await integration.async_get_platform("light") == hue_light

    # Hue is loaded and the last call should have cached the import_module failure
    with pytest.raises(ModuleNotFoundError):
        assert await integration.async_get_platform("light") == hue_light

    # The cache should never be filled because the import error is remembered
    assert integration.get_platform_cached("light") is None