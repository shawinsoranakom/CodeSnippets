async def test_service_group_services_add_remove_entities(hass: HomeAssistant) -> None:
    """Check if we can add and remove entities from group."""

    hass.states.async_set("person.one", "Work")
    hass.states.async_set("person.two", "Work")
    hass.states.async_set("person.three", "home")

    assert await async_setup_component(hass, "person", {})
    with assert_setup_component(0, "group"):
        await async_setup_component(hass, "group", {"group": {}})
    await hass.async_block_till_done()

    assert hass.services.has_service("group", group.SERVICE_SET)

    await hass.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {
            "object_id": "new_group",
            "name": "New Group",
            "entities": ["person.one", "person.two"],
        },
    )
    await hass.async_block_till_done()

    group_state = hass.states.get("group.new_group")
    assert group_state.state == "not_home"
    assert group_state.attributes["friendly_name"] == "New Group"
    assert list(group_state.attributes["entity_id"]) == ["person.one", "person.two"]

    await hass.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {
            "object_id": "new_group",
            "add_entities": "person.three",
        },
    )
    await hass.async_block_till_done()
    group_state = hass.states.get("group.new_group")
    assert group_state.state == "home"
    assert "person.three" in list(group_state.attributes["entity_id"])

    await hass.services.async_call(
        group.DOMAIN,
        group.SERVICE_SET,
        {
            "object_id": "new_group",
            "remove_entities": "person.one",
        },
    )
    await hass.async_block_till_done()
    group_state = hass.states.get("group.new_group")
    assert group_state.state == "home"
    assert "person.one" not in list(group_state.attributes["entity_id"])