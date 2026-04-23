async def test_is_on_and_state_mixed_domains(
    hass: HomeAssistant,
    domains: tuple[str, ...],
    states_old: tuple[str, ...],
    states_new: tuple[str, ...],
    state_ison_group_old: tuple[str, bool],
    state_ison_group_new: tuple[str, bool],
) -> None:
    """Test is_on method with mixed domains."""
    count = len(domains)
    entity_ids = [f"{domains[index]}.test_{index}" for index in range(count)]
    for index in range(count):
        hass.states.async_set(entity_ids[index], states_old[index])

    assert not group.is_on(hass, "group.none")
    await asyncio.gather(
        *[async_setup_component(hass, domain, {}) for domain in set(domains)]
    )
    assert await async_setup_component(hass, "group", {})
    await hass.async_block_till_done()

    test_group = await group.Group.async_create_group(
        hass,
        "init_group",
        created_by_service=True,
        entity_ids=entity_ids,
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    await hass.async_block_till_done()

    # Assert on old state
    state = hass.states.get(test_group.entity_id)
    assert state is not None
    assert state.state == state_ison_group_old[0]
    assert group.is_on(hass, test_group.entity_id) == state_ison_group_old[1]

    # Switch and assert on new state
    for index in range(count):
        hass.states.async_set(entity_ids[index], states_new[index])
    await hass.async_block_till_done()
    state = hass.states.get(test_group.entity_id)
    assert state is not None
    assert state.state == state_ison_group_new[0]
    assert group.is_on(hass, test_group.entity_id) == state_ison_group_new[1]