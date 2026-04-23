async def test_reload_platform(hass: HomeAssistant) -> None:
    """Test the polling of only updated entities."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    assert component_setup.called

    assert f"{PLATFORM}.{DOMAIN}" in hass.config.components
    assert len(setup_called) == 1

    platform = async_get_platform_without_config_entry(hass, PLATFORM, DOMAIN)
    assert platform.platform_name == PLATFORM
    assert platform.domain == DOMAIN

    yaml_path = get_fixture_path("helpers/reload_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await async_reload_integration_platforms(hass, PLATFORM, [DOMAIN])

    assert len(setup_called) == 2

    existing_platforms = async_get_platforms(hass, PLATFORM)
    for existing_platform in existing_platforms:
        existing_platform.config_entry = "abc"
    assert not async_get_platform_without_config_entry(hass, PLATFORM, DOMAIN)