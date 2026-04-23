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
                "dt1": {"has_time": False, "has_date": True, "initial": "2019-1-1"},
                "dt3": {CONF_HAS_TIME: True, CONF_HAS_DATE: True},
            }
        },
    )

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_datetime.dt1")
    state_2 = hass.states.get("input_datetime.dt2")
    state_3 = hass.states.get("input_datetime.dt3")

    dt_obj = datetime.datetime(2019, 1, 1, 0, 0)
    assert state_1 is not None
    assert state_2 is None
    assert state_3 is not None
    assert dt_obj.strftime(FORMAT_DATE) == state_1.state
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt1") == f"{DOMAIN}.dt1"
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt2") is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt3") == f"{DOMAIN}.dt3"

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "dt1": {"has_time": True, "has_date": False, "initial": "23:32"},
                "dt2": {"has_time": True, "has_date": True},
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

    state_1 = hass.states.get("input_datetime.dt1")
    state_2 = hass.states.get("input_datetime.dt2")
    state_3 = hass.states.get("input_datetime.dt3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is None
    assert state_1.state == DEFAULT_TIME.strftime(FORMAT_TIME)
    assert state_2.state == datetime.datetime.combine(
        datetime.date.today(), DEFAULT_TIME
    ).strftime(FORMAT_DATETIME)

    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt1") == f"{DOMAIN}.dt1"
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt2") == f"{DOMAIN}.dt2"
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "dt3") is None