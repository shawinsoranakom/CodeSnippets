async def test_service_group_set_group_remove_group(hass: HomeAssistant) -> None:
    """Check if service are available."""
    with assert_setup_component(0, "group"):
        await async_setup_component(hass, "group", {"group": {}})

    common.async_set_group(hass, "user_test_group", name="Test")
    await hass.async_block_till_done()

    group_state = hass.states.get("group.user_test_group")
    assert group_state
    assert group_state.attributes[group.ATTR_AUTO]
    assert group_state.attributes["friendly_name"] == "Test"

    common.async_set_group(hass, "user_test_group", entity_ids=["test.entity_bla1"])
    await hass.async_block_till_done()

    group_state = hass.states.get("group.user_test_group")
    assert group_state
    assert group_state.attributes[group.ATTR_AUTO]
    assert group_state.attributes["friendly_name"] == "Test"
    assert list(group_state.attributes["entity_id"]) == ["test.entity_bla1"]

    common.async_set_group(
        hass,
        "user_test_group",
        icon="mdi:camera",
        name="Test2",
        add=["test.entity_id2"],
    )
    await hass.async_block_till_done()

    group_state = hass.states.get("group.user_test_group")
    assert group_state
    assert group_state.attributes[group.ATTR_AUTO]
    assert group_state.attributes["friendly_name"] == "Test2"
    assert group_state.attributes["icon"] == "mdi:camera"
    assert sorted(group_state.attributes["entity_id"]) == sorted(
        ["test.entity_bla1", "test.entity_id2"]
    )

    common.async_remove(hass, "user_test_group")
    await hass.async_block_till_done()

    group_state = hass.states.get("group.user_test_group")
    assert group_state is None