async def test_get_translations_loads_config_flows(
    hass: HomeAssistant, mock_config_flows
) -> None:
    """Test the get translations helper loads config flow translations."""
    mock_config_flows["integration"].append("component1")
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 1"

    with (
        patch(
            "homeassistant.helpers.translation._load_translations_files_by_language",
            return_value={"en": {"component1": {"title": "world"}}},
        ),
        patch(
            "homeassistant.helpers.translation.async_get_integrations",
            return_value={"component1": integration},
        ),
    ):
        translations = await translation.async_get_translations(
            hass, "en", "title", config_flow=True
        )
        translations_again = await translation.async_get_translations(
            hass, "en", "title", config_flow=True
        )

        assert translations == translations_again

    assert translations == {
        "component.component1.title": "world",
    }

    assert "component1" not in hass.config.components

    mock_config_flows["integration"].append("component2")
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 2"

    with (
        patch(
            "homeassistant.helpers.translation._load_translations_files_by_language",
            return_value={"en": {"component2": {"title": "world"}}},
        ),
        patch(
            "homeassistant.helpers.translation.async_get_integrations",
            return_value={"component2": integration},
        ),
    ):
        translations = await translation.async_get_translations(
            hass, "en", "title", config_flow=True
        )
        translations_again = await translation.async_get_translations(
            hass, "en", "title", config_flow=True
        )

        assert translations == translations_again

    assert translations == {
        "component.component1.title": "world",
        "component.component2.title": "world",
    }

    translations_all_cached = await translation.async_get_translations(
        hass, "en", "title", config_flow=True
    )
    assert translations == translations_all_cached

    assert "component1" not in hass.config.components
    assert "component2" not in hass.config.components