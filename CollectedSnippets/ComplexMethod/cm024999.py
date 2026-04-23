async def test_caching(hass: HomeAssistant) -> None:
    """Test we cache data."""
    hass.config.components.add("binary_sensor")
    hass.config.components.add("switch")

    # Patch with same method so we can count invocations
    with patch(
        "homeassistant.helpers.icon.build_resources",
        side_effect=icon.build_resources,
    ) as mock_build:
        load1 = await icon.async_get_icons(hass, "entity_component")
        # conditions, entity_component, services, triggers
        assert len(mock_build.mock_calls) == 4

        load2 = await icon.async_get_icons(hass, "entity_component")
        # conditions, entity_component, services, triggers
        assert len(mock_build.mock_calls) == 4

        assert load1 == load2

        assert load1["binary_sensor"]
        assert load1["switch"]

    load_switch_only = await icon.async_get_icons(
        hass, "entity_component", integrations={"switch"}
    )
    assert load_switch_only
    assert list(load_switch_only) == ["switch"]

    load_binary_sensor_only = await icon.async_get_icons(
        hass, "entity_component", integrations={"binary_sensor"}
    )
    assert load_binary_sensor_only
    assert list(load_binary_sensor_only) == ["binary_sensor"]

    # Check if new loaded component, trigger load
    hass.config.components.add("media_player")
    with patch(
        "homeassistant.helpers.icon._load_icons_files",
        side_effect=icon._load_icons_files,
    ) as mock_load:
        load_sensor_only = await icon.async_get_icons(
            hass, "entity_component", integrations={"switch"}
        )
        assert load_sensor_only
        assert len(mock_load.mock_calls) == 0

        await icon.async_get_icons(
            hass, "entity_component", integrations={"media_player"}
        )
        assert len(mock_load.mock_calls) == 1