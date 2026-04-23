async def test_reload(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, hass_admin_user: MockUser
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": None,
                "test_2": {"name": "Hello World", "icon": "mdi:work"},
            }
        },
    )

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_button.test_1")
    state_2 = hass.states.get("input_button.test_2")
    state_3 = hass.states.get("input_button.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None

    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is None

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    "name": "Hello World reloaded",
                    "icon": "mdi:work_reloaded",
                },
                "test_3": None,
            }
        },
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_button.test_1")
    state_2 = hass.states.get("input_button.test_2")
    state_3 = hass.states.get("input_button.test_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_3 is not None

    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None