async def assert_condition_behavior_any(
    hass: HomeAssistant,
    *,
    target_entities: dict[str, list[str]],
    condition_target_config: dict,
    entity_id: str,
    entities_in_target: int,
    condition: str,
    condition_options: dict[str, Any],
    states: list[ConditionStateDescription],
) -> None:
    """Test condition with the 'any' behavior."""
    other_entity_ids = set(target_entities["included_entities"]) - {entity_id}
    excluded_entity_ids = set(target_entities["excluded_entities"]) - {entity_id}

    for eid in target_entities["included_entities"]:
        set_or_remove_state(hass, eid, states[0]["included_state"])
        await hass.async_block_till_done()
    for eid in excluded_entity_ids:
        set_or_remove_state(hass, eid, states[0]["excluded_state"])
        await hass.async_block_till_done()

    cond = await create_target_condition(
        hass,
        condition=condition,
        target=condition_target_config,
        behavior="any",
        condition_options=condition_options,
    )

    for state in states:
        included_state = state["included_state"]
        excluded_state = state["excluded_state"]

        # Set excluded entities first to verify that they don't make the
        # condition evaluate to true
        for excluded_entity_id in excluded_entity_ids:
            set_or_remove_state(hass, excluded_entity_id, excluded_state)
            await hass.async_block_till_done()
        assert cond(hass) is False

        set_or_remove_state(hass, entity_id, included_state)
        await hass.async_block_till_done()
        assert cond(hass) == state["condition_true"]

        # Set other included entities to the included state to verify that
        # they don't change the condition evaluation
        for other_entity_id in other_entity_ids:
            set_or_remove_state(hass, other_entity_id, included_state)
            await hass.async_block_till_done()
        assert cond(hass) == state["condition_true"]