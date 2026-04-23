async def test_setup(hass: HomeAssistant) -> None:
    """Test setup method."""
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    group_conf = OrderedDict()
    group_conf["test_group"] = "hello.world,sensor.happy"
    group_conf["empty_group"] = {"name": "Empty Group", "entities": None}
    assert await async_setup_component(hass, "light", {})
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "group", {"group": group_conf})
    await hass.async_block_till_done()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=["light.Bowl", "light.Ceiling"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    await group.Group.async_create_group(
        hass,
        "created_group",
        created_by_service=False,
        entity_ids=["light.Bowl", f"{test_group.entity_id}"],
        icon="mdi:work",
        mode=None,
        object_id=None,
        order=None,
    )
    await hass.async_block_till_done()

    group_state = hass.states.get(f"{group.DOMAIN}.created_group")
    assert group_state.state == STATE_ON
    assert {test_group.entity_id, "light.bowl"} == set(
        group_state.attributes["entity_id"]
    )
    assert group_state.attributes.get(group.ATTR_AUTO) is None
    assert group_state.attributes.get(ATTR_ICON) == "mdi:work"
    assert group_state.attributes.get(group.ATTR_ORDER) == 3

    group_state = hass.states.get(f"{group.DOMAIN}.test_group")
    assert group_state.state == STATE_UNKNOWN
    assert set(group_state.attributes["entity_id"]) == {"sensor.happy", "hello.world"}
    assert group_state.attributes.get(group.ATTR_AUTO) is None
    assert group_state.attributes.get(ATTR_ICON) is None
    assert group_state.attributes.get(group.ATTR_ORDER) == 0