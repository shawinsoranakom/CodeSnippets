async def assert_trigger_behavior_last(
    hass: HomeAssistant,
    *,
    target_entities: dict[str, list[str]],
    trigger_target_config: dict,
    entity_id: str,
    entities_in_target: int,
    trigger: str,
    trigger_options: dict[str, Any],
    states: list[TriggerStateDescription],
) -> None:
    """Test trigger fires in mode last."""
    calls: list[str] = []
    other_entity_ids = set(target_entities["included_entities"]) - {entity_id}
    excluded_entity_ids = set(target_entities["excluded_entities"]) - {entity_id}

    for eid in target_entities["included_entities"]:
        set_or_remove_state(hass, eid, states[0]["included_state"])
        await hass.async_block_till_done()
    for eid in excluded_entity_ids:
        set_or_remove_state(hass, eid, states[0]["excluded_state"])
        await hass.async_block_till_done()

    await arm_trigger(
        hass,
        trigger,
        {"behavior": "last"} | trigger_options,
        trigger_target_config,
        calls,
    )

    for state in states[1:]:
        excluded_state = state["excluded_state"]
        included_state = state["included_state"]
        for other_entity_id in other_entity_ids:
            set_or_remove_state(hass, other_entity_id, included_state)
            await hass.async_block_till_done()
        assert len(calls) == 0

        set_or_remove_state(hass, entity_id, included_state)
        await hass.async_block_till_done()
        assert len(calls) == state["count"]
        for call in calls:
            assert call == entity_id
        calls.clear()

        for excluded_entity_id in excluded_entity_ids:
            set_or_remove_state(hass, excluded_entity_id, excluded_state)
            await hass.async_block_till_done()
        assert len(calls) == 0