async def test_caching(hass: HomeAssistant) -> None:
    """Test we cache data."""
    hass.config.components.add("sensor")
    hass.config.components.add("light")

    # Patch with same method so we can count invocations
    with patch(
        "homeassistant.helpers.translation.build_resources",
        side_effect=translation.build_resources,
    ) as mock_build_resources:
        load1 = await translation.async_get_translations(hass, "en", "entity_component")
        assert len(mock_build_resources.mock_calls) == 9

        load2 = await translation.async_get_translations(hass, "en", "entity_component")
        assert len(mock_build_resources.mock_calls) == 9

        assert load1 == load2

        for key in load1:
            assert key.startswith(
                (
                    "component.sensor.entity_component.",
                    "component.light.entity_component.",
                )
            )

    load_sensor_only = await translation.async_get_translations(
        hass, "en", "entity_component", integrations={"sensor"}
    )
    assert load_sensor_only
    for key in load_sensor_only:
        assert key.startswith("component.sensor.entity_component.")

    load_light_only = await translation.async_get_translations(
        hass, "en", "entity_component", integrations={"light"}
    )
    assert load_light_only
    for key in load_light_only:
        assert key.startswith("component.light.entity_component.")

    hass.config.components.add("media_player")

    # Patch with same method so we can count invocations
    with patch(
        "homeassistant.helpers.translation.build_resources",
        side_effect=translation.build_resources,
    ) as mock_build:
        load_sensor_only = await translation.async_get_translations(
            hass, "en", "title", integrations={"sensor"}
        )
        assert load_sensor_only
        for key in load_sensor_only:
            assert key == "component.sensor.title"
        assert len(mock_build.mock_calls) == 0

        assert await translation.async_get_translations(
            hass, "en", "title", integrations={"sensor"}
        )
        assert len(mock_build.mock_calls) == 0

        load_light_only = await translation.async_get_translations(
            hass, "en", "title", integrations={"media_player"}
        )
        assert load_light_only
        for key in load_light_only:
            assert key == "component.media_player.title"
        assert len(mock_build.mock_calls) > 1