async def help_test_mixed_entity_platforms_on_off_state_test(
    hass: HomeAssistant,
    on_off_states1: tuple[set[str], str, str],
    on_off_states2: tuple[set[str], str, str],
    entity_and_state1_state_2: tuple[str, str | None, str | None],
    group_state1: str,
    group_state2: str,
    grouped_groups: bool = False,
) -> None:
    """Help test on_off_states on mixed entity platforms."""

    class MockGroupPlatform1(MockPlatform):
        """Mock a group platform module for test1 integration."""

        def async_describe_on_off_states(
            self, hass: HomeAssistant, registry: GroupIntegrationRegistry
        ) -> None:
            """Describe group on off states."""
            registry.on_off_states("test1", *on_off_states1)

    class MockGroupPlatform2(MockPlatform):
        """Mock a group platform module for test2 integration."""

        def async_describe_on_off_states(
            self, hass: HomeAssistant, registry: GroupIntegrationRegistry
        ) -> None:
            """Describe group on off states."""
            registry.on_off_states("test2", *on_off_states2)

    mock_integration(hass, MockModule(domain="test1"))
    mock_platform(hass, "test1.group", MockGroupPlatform1())
    assert await async_setup_component(hass, "test1", {"test1": {}})

    mock_integration(hass, MockModule(domain="test2"))
    mock_platform(hass, "test2.group", MockGroupPlatform2())
    assert await async_setup_component(hass, "test2", {"test2": {}})

    if grouped_groups:
        assert await async_setup_component(
            hass,
            "group",
            {
                "group": {
                    "test1": {
                        "entities": [
                            item[0]
                            for item in entity_and_state1_state_2
                            if item[0].startswith("test1.")
                        ]
                    },
                    "test2": {
                        "entities": [
                            item[0]
                            for item in entity_and_state1_state_2
                            if item[0].startswith("test2.")
                        ]
                    },
                    "test": {"entities": ["group.test1", "group.test2"]},
                }
            },
        )
    else:
        assert await async_setup_component(
            hass,
            "group",
            {
                "group": {
                    "test": {
                        "entities": [item[0] for item in entity_and_state1_state_2]
                    },
                }
            },
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("group.test")
    assert state is not None

    # Set first state
    for entity_id, state1, _ in entity_and_state1_state_2:
        hass.states.async_set(entity_id, state1)

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("group.test")
    assert state is not None
    assert state.state == group_state1

    # Set second state
    for entity_id, _, state2 in entity_and_state1_state_2:
        hass.states.async_set(entity_id, state2)

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("group.test")
    assert state is not None
    assert state.state == group_state2