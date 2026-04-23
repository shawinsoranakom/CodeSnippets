async def test_async_get_component_preloads_config_and_config_flow(
    hass: HomeAssistant,
) -> None:
    """Verify async_get_component will try to preload the config and config_flow platform."""
    executor_import_integration = _get_test_integration(
        hass, "executor_import", True, import_executor=True
    )
    assert executor_import_integration.import_executor is True

    assert "homeassistant.components.executor_import" not in sys.modules
    assert "custom_components.executor_import" not in sys.modules

    platform_exists_calls = []

    def mock_platforms_exists(platforms: list[str]) -> bool:
        platform_exists_calls.append(platforms)
        return platforms

    with (
        patch("homeassistant.loader.importlib.import_module") as mock_import,
        patch.object(
            executor_import_integration, "platforms_exists", mock_platforms_exists
        ),
    ):
        await executor_import_integration.async_get_component()

    assert len(platform_exists_calls[0]) == len(loader.BASE_PRELOAD_PLATFORMS)
    assert mock_import.call_count == 1 + len(loader.BASE_PRELOAD_PLATFORMS)
    assert (
        mock_import.call_args_list[0][0][0]
        == "homeassistant.components.executor_import"
    )
    checked_platforms = {
        mock_import.call_args_list[i][0][0]
        for i in range(1, len(mock_import.call_args_list))
    }
    assert checked_platforms == {
        "homeassistant.components.executor_import.config_flow",
        *(
            f"homeassistant.components.executor_import.{platform}"
            for platform in loader.BASE_PRELOAD_PLATFORMS
        ),
    }