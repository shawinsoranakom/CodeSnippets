async def test_reload(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    """Test reloading the YAML config."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {"name": "Person 1", "id": "id-1"},
                {"name": "Person 2", "id": "id-2"},
            ]
        },
    )

    assert len(hass.states.async_entity_ids()) == 3  # Person1, Person2, zone.home

    state_1 = hass.states.get("person.person_1")
    state_2 = hass.states.get("person.person_2")
    state_3 = hass.states.get("person.person_3")

    assert state_1 is not None
    assert state_1.name == "Person 1"
    assert state_2 is not None
    assert state_2.name == "Person 2"
    assert state_3 is None

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: [
                {"name": "Person 1-updated", "id": "id-1"},
                {"name": "Person 3", "id": "id-3"},
            ]
        },
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
        await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) == 3  # Person1, Person2, zone.home

    state_1 = hass.states.get("person.person_1")
    state_2 = hass.states.get("person.person_2")
    state_3 = hass.states.get("person.person_3")

    assert state_1 is not None
    assert state_1.name == "Person 1-updated"
    assert state_2 is None
    assert state_3 is not None
    assert state_3.name == "Person 3"