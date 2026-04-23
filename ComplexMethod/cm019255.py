async def test_group_order_with_dynamic_creation(hass: HomeAssistant) -> None:
    """Test that order gets incremented when creating a new group."""
    hass.states.async_set("light.bowl", STATE_ON)

    assert await async_setup_component(hass, "light", {})
    assert await async_setup_component(
        hass,
        "group",
        {
            "group": {
                "group_zero": {"entities": "light.Bowl", "icon": "mdi:work"},
                "group_one": {"entities": "light.Bowl", "icon": "mdi:work"},
                "group_two": {"entities": "light.Bowl", "icon": "mdi:work"},
            }
        },
    )
    await hass.async_block_till_done()

    assert hass.states.get("group.group_zero").attributes["order"] == 0
    assert hass.states.get("group.group_one").attributes["order"] == 1
    assert hass.states.get("group.group_two").attributes["order"] == 2

    await hass.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {"object_id": "new_group", "name": "New Group", "entities": "light.bowl"},
    )
    await hass.async_block_till_done()

    assert hass.states.get("group.new_group").attributes["order"] == 3

    await hass.services.async_call(
        group.DOMAIN,
        group.SERVICE_REMOVE,
        {
            "object_id": "new_group",
        },
    )
    await hass.async_block_till_done()

    assert not hass.states.get("group.new_group")

    await hass.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {"object_id": "new_group2", "name": "New Group 2", "entities": "light.bowl"},
    )
    await hass.async_block_till_done()

    assert hass.states.get("group.new_group2").attributes["order"] == 4