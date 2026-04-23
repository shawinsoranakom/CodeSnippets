async def test_reload(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_admin_user: MockUser,
    hass_read_only_user: MockUser,
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    assert await setup.async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {"name": "yaml 1", "latitude": 1, "longitude": 2},
                {"name": "yaml 2", "latitude": 3, "longitude": 4},
            ],
        },
    )

    assert count_start + 3 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("zone.yaml_1")
    state_2 = hass.states.get("zone.yaml_2")
    state_3 = hass.states.get("zone.yaml_3")

    assert state_1 is not None
    assert state_1.attributes["latitude"] == 1
    assert state_1.attributes["longitude"] == 2
    assert state_2 is not None
    assert state_2.attributes["latitude"] == 3
    assert state_2.attributes["longitude"] == 4
    assert state_3 is None
    assert len(entity_registry.entities) == 0

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: [
                {"name": "yaml 2", "latitude": 3, "longitude": 4},
                {"name": "yaml 3", "latitude": 5, "longitude": 6},
            ]
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

    assert count_start + 3 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("zone.yaml_1")
    state_2 = hass.states.get("zone.yaml_2")
    state_3 = hass.states.get("zone.yaml_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_2.attributes["latitude"] == 3
    assert state_2.attributes["longitude"] == 4
    assert state_3 is not None
    assert state_3.attributes["latitude"] == 5
    assert state_3.attributes["longitude"] == 6