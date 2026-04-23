async def test_reload_core_conf(hass: HomeAssistant) -> None:
    """Test reload core conf service."""
    await async_setup_component(hass, ha.DOMAIN, {})
    ent = entity.Entity()
    ent.entity_id = "test.entity"
    ent.hass = hass
    platform = MockEntityPlatform(hass, domain="test", platform_name="test")
    await platform.async_add_entities([ent])
    ent.async_write_ha_state()

    state = hass.states.get("test.entity")
    assert state is not None
    assert state.state == "unknown"
    assert state.attributes == {}

    files = {
        config.YAML_CONFIG_FILE: yaml.dump(
            {
                ha.DOMAIN: {
                    "country": "SE",  # To avoid creating issue country_not_configured
                    "latitude": 10,
                    "longitude": 20,
                    "customize": {"test.Entity": {"hello": "world"}},
                }
            }
        )
    }
    with patch_yaml_files(files, True):
        await hass.services.async_call(
            ha.DOMAIN, SERVICE_RELOAD_CORE_CONFIG, blocking=True
        )

    assert hass.config.latitude == 10
    assert hass.config.longitude == 20

    ent.async_write_ha_state()

    state = hass.states.get("test.entity")
    assert state is not None
    assert state.state == "unknown"
    assert state.attributes.get("hello") == "world"