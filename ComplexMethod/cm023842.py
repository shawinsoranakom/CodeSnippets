async def test_reload(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_admin_user: MockUser,
    hass_read_only_user: MockUser,
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": {
                    "options": ["first option", "middle option", "last option"],
                    "initial": "middle option",
                },
                "test_2": {
                    "options": ["an option", "not an option"],
                    "initial": "an option",
                },
            }
        },
    )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_select.test_1")
    state_2 = hass.states.get("input_select.test_2")
    state_3 = hass.states.get("input_select.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert state_1.state == "middle option"
    assert state_2.state == "an option"
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is None

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    "options": ["an option", "reloaded option"],
                    "initial": "reloaded option",
                },
                "test_3": {
                    "options": ["new option", "newer option"],
                    "initial": "newer option",
                },
            }
        },
    ):
        with pytest.raises(Unauthorized):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id=hass_read_only_user.id),
            )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_select.test_1")
    state_2 = hass.states.get("input_select.test_2")
    state_3 = hass.states.get("input_select.test_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_3 is not None
    assert state_2.state == "an option"
    assert state_3.state == "newer option"
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None