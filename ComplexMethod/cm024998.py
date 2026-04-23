async def test_get_icons(hass: HomeAssistant) -> None:
    """Test the get icon helper."""
    icons = await icon.async_get_icons(hass, "entity")
    assert icons == {}

    icons = await icon.async_get_icons(hass, "entity_component")
    assert icons == {}

    # Set up test switch component
    assert await async_setup_component(hass, "switch", {"switch": {"platform": "test"}})

    # Test getting icons for the entity component
    icons = await icon.async_get_icons(hass, "entity_component")
    assert icons["switch"]["_"]["default"] == "mdi:toggle-switch-variant"

    # Test services icons are available
    icons = await icon.async_get_icons(hass, "services")
    assert len(icons) == 1
    assert icons["switch"]["turn_off"] == {"service": "mdi:toggle-switch-variant-off"}

    # Ensure icons file for platform isn't loaded, as that isn't supported
    icons = await icon.async_get_icons(hass, "entity")
    assert icons == {}
    with pytest.raises(ValueError, match="test.switch"):
        await icon.async_get_icons(hass, "entity", ["test.switch"])

    # Load up an custom integration
    hass.config.components.add("test_package")
    await hass.async_block_till_done()

    icons = await icon.async_get_icons(hass, "entity")
    assert len(icons) == 1

    assert icons == {
        "test_package": {
            "switch": {
                "something": {"state": {"away": "mdi:home-outline", "home": "mdi:home"}}
            }
        }
    }

    icons = await icon.async_get_icons(hass, "services")
    assert len(icons) == 2
    assert icons["test_package"]["enable_god_mode"] == {"service": "mdi:shield"}

    # Load another one
    hass.config.components.add("test_embedded")
    await hass.async_block_till_done()

    icons = await icon.async_get_icons(hass, "entity")
    assert len(icons) == 2

    assert icons["test_package"] == {
        "switch": {
            "something": {"state": {"away": "mdi:home-outline", "home": "mdi:home"}}
        }
    }

    # Test getting non-existing integration
    with pytest.raises(
        IntegrationNotFound, match="Integration 'non_existing' not found"
    ):
        await icon.async_get_icons(hass, "entity", ["non_existing"])