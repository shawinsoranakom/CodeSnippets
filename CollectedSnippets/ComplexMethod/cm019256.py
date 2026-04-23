async def test_group_that_references_two_types_of_groups(hass: HomeAssistant) -> None:
    """Group that references a group of covers and device_trackers."""

    group_1_entity_ids = [
        "cover.living_front_ri",
        "cover.living_back_lef",
    ]
    group_2_entity_ids = [
        "device_tracker.living_front_ri",
        "device_tracker.living_back_lef",
    ]
    hass.set_state(CoreState.stopped)

    for entity_id in group_1_entity_ids:
        hass.states.async_set(entity_id, "closed")
    for entity_id in group_2_entity_ids:
        hass.states.async_set(entity_id, "home")
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "cover", {})
    assert await async_setup_component(hass, "device_tracker", {})
    assert await async_setup_component(
        hass,
        "group",
        {
            "group": {
                "covers": {"entities": group_1_entity_ids},
                "device_trackers": {"entities": group_2_entity_ids},
                "grouped_group": {
                    "entities": ["group.covers", "group.device_trackers"]
                },
            }
        },
    )
    assert await async_setup_component(hass, "cover", {})
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    assert hass.states.get("group.covers").state == "closed"
    assert hass.states.get("group.device_trackers").state == "home"
    assert hass.states.get("group.grouped_group").state == "on"