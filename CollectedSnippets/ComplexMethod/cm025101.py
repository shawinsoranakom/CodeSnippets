async def test_expand(hass: HomeAssistant) -> None:
    """Test expand function."""
    info = render_to_info(hass, "{{ expand('test.object') }}")
    assert_result_info(info, [], ["test.object"])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ expand(56) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    hass.states.async_set("test.object", "happy")

    info = render_to_info(
        hass,
        "{{ expand('test.object') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "test.object", ["test.object"])
    assert info.rate_limit is None

    info = render_to_info(
        hass,
        "{{ expand('group.new_group') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "", ["group.new_group"])
    assert info.rate_limit is None

    info = render_to_info(
        hass,
        "{{ expand(states.group) | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "", [], ["group"])
    assert info.rate_limit == DOMAIN_STATES_RATE_LIMIT

    assert await async_setup_component(hass, "group", {})
    await hass.async_block_till_done()
    await group.Group.async_create_group(
        hass,
        "new group",
        created_by_service=False,
        entity_ids=["test.object"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    info = render_to_info(
        hass,
        "{{ expand('group.new_group') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "test.object", {"group.new_group", "test.object"})
    assert info.rate_limit is None

    info = render_to_info(
        hass,
        "{{ expand(states.group) | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "test.object", {"test.object"}, ["group"])
    assert info.rate_limit == DOMAIN_STATES_RATE_LIMIT

    info = render_to_info(
        hass,
        (
            "{{ expand('group.new_group', 'test.object')"
            " | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}"
        ),
    )
    assert_result_info(info, "test.object", {"test.object", "group.new_group"})

    info = render_to_info(
        hass,
        (
            "{{ ['group.new_group', 'test.object'] | expand"
            " | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}"
        ),
    )
    assert_result_info(info, "test.object", {"test.object", "group.new_group"})
    assert info.rate_limit is None

    hass.states.async_set("sensor.power_1", 0)
    hass.states.async_set("sensor.power_2", 200.2)
    hass.states.async_set("sensor.power_3", 400.4)

    assert await async_setup_component(hass, "group", {})
    await hass.async_block_till_done()
    await group.Group.async_create_group(
        hass,
        "power sensors",
        created_by_service=False,
        entity_ids=["sensor.power_1", "sensor.power_2", "sensor.power_3"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    info = render_to_info(
        hass,
        (
            "{{ states.group.power_sensors.attributes.entity_id | expand "
            "| sort(attribute='entity_id') | map(attribute='state')|map('float')|sum  }}"
        ),
    )
    assert_result_info(
        info,
        200.2 + 400.4,
        {"group.power_sensors", "sensor.power_1", "sensor.power_2", "sensor.power_3"},
    )
    assert info.rate_limit is None

    # With group entities
    hass.states.async_set("light.first", "on")
    hass.states.async_set("light.second", "off")

    assert await async_setup_component(
        hass,
        "light",
        {
            "light": {
                "platform": "group",
                "name": "Grouped",
                "entities": ["light.first", "light.second"],
            }
        },
    )
    await hass.async_block_till_done()

    info = render_to_info(
        hass,
        "{{ expand('light.grouped') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(
        info,
        "light.first, light.second",
        ["light.grouped", "light.first", "light.second"],
    )

    assert await async_setup_component(
        hass,
        "zone",
        {
            "zone": {
                "name": "Test",
                "latitude": 32.880837,
                "longitude": -117.237561,
                "radius": 250,
                "passive": False,
            }
        },
    )
    info = render_to_info(
        hass,
        "{{ expand('zone.test') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(
        info,
        "",
        ["zone.test"],
    )

    hass.states.async_set(
        "person.person1",
        "test",
    )
    await hass.async_block_till_done()

    info = render_to_info(
        hass,
        "{{ expand('zone.test') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(
        info,
        "person.person1",
        ["zone.test", "person.person1"],
    )

    hass.states.async_set(
        "person.person2",
        "test",
    )
    await hass.async_block_till_done()

    info = render_to_info(
        hass,
        "{{ expand('zone.test') | sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(
        info,
        "person.person1, person.person2",
        ["zone.test", "person.person1", "person.person2"],
    )