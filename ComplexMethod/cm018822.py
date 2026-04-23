async def test_reload(
    hass: HomeAssistant, hass_admin_user: MockUser, hass_read_only_user: MockUser
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    assert await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: {"test_1": {"initial": "test 1"}, "test_2": {"initial": "test 2"}}},
    )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_text.test_1")
    state_2 = hass.states.get("input_text.test_2")
    state_3 = hass.states.get("input_text.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert state_1.state == "test 1"
    assert state_2.state == "test 2"
    assert state_1.attributes[ATTR_MIN] == 0
    assert state_2.attributes[ATTR_MAX] == 100

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {"initial": "test reloaded", ATTR_MIN: 12},
                "test_3": {"initial": "test 3", ATTR_MAX: 21},
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

    state_1 = hass.states.get("input_text.test_1")
    state_2 = hass.states.get("input_text.test_2")
    state_3 = hass.states.get("input_text.test_3")

    assert state_1 is None
    assert state_2 is not None
    assert state_3 is not None
    assert state_2.attributes[ATTR_MIN] == 12
    assert state_3.attributes[ATTR_MAX] == 21