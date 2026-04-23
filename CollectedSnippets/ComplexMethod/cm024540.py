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
                "test_1": {"initial": 50, "min": 0, "max": 51},
                "test_3": {"initial": 10, "min": 0, "max": 15},
            }
        },
    )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_number.test_1")
    state_2 = hass.states.get("input_number.test_2")
    state_3 = hass.states.get("input_number.test_3")

    assert state_1 is not None
    assert state_2 is None
    assert state_3 is not None
    assert float(state_1.state) == 50
    assert float(state_3.state) == 10
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_1": {"initial": 40, "min": 0, "max": 51},
                "test_2": {"initial": 20, "min": 10, "max": 30},
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
        await hass.async_block_till_done()

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_number.test_1")
    state_2 = hass.states.get("input_number.test_2")
    state_3 = hass.states.get("input_number.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert float(state_1.state) == 50
    assert float(state_2.state) == 20
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is None