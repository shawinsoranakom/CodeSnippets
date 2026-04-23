async def assert_numerical_condition_unit_conversion(
    hass: HomeAssistant,
    *,
    condition: str,
    entity_id: str,
    pass_states: list[StateDescription],
    fail_states: list[StateDescription],
    numerical_condition_options: list[dict[str, Any]],
    limit_entity_condition_options: dict[str, Any],
    limit_entities: tuple[str, str],
    limit_entity_states: list[tuple[StateDescription, StateDescription]],
    invalid_limit_entity_states: list[tuple[StateDescription, StateDescription]],
) -> None:
    """Test unit conversion of a numerical condition.

    Verifies that a numerical condition correctly converts between units, both
    when limits are specified as numbers (with explicit units) and when limits
    come from entity references. Also verifies that the condition rejects limit
    entities whose unit_of_measurement is invalid (not convertible).

    Args:
        condition: The condition key (e.g. "climate.target_temperature").
        entity_id: The entity being evaluated by the condition.
        pass_states: Entity states that should make the condition pass.
        fail_states: Entity states that should make the condition fail.
        numerical_condition_options: List of condition option dicts, each
            specifying above/below thresholds with a unit. Every combination
            is tested against pass_states and fail_states.
        limit_entity_condition_options: Condition options dict using entity
            references for above/below (e.g. {CONF_ABOVE: "sensor.above"}).
        limit_entities: Tuple of (above_entity_id, below_entity_id) referenced
            by limit_entity_condition_options.
        limit_entity_states: List of (above_state, below_state) tuples, each
            providing valid states for the limit entities. Every combination
            is tested against pass_states and fail_states.
        invalid_limit_entity_states: Like limit_entity_states, but with invalid
            units. The condition should always fail regardless of entity state.

    """
    # Test limits set as number
    for condition_options in numerical_condition_options:
        cond = await create_target_condition(
            hass,
            condition=condition,
            target={CONF_ENTITY_ID: [entity_id]},
            behavior="any",
            condition_options=condition_options,
        )
        for state in pass_states:
            set_or_remove_state(hass, entity_id, state)
            assert cond(hass) is True
        for state in fail_states:
            set_or_remove_state(hass, entity_id, state)
            assert cond(hass) is False

    # Test limits set by entity
    cond = await create_target_condition(
        hass,
        condition=condition,
        target={CONF_ENTITY_ID: [entity_id]},
        behavior="any",
        condition_options=limit_entity_condition_options,
    )
    for limit_states in limit_entity_states:
        set_or_remove_state(hass, limit_entities[0], limit_states[0])
        set_or_remove_state(hass, limit_entities[1], limit_states[1])
        for state in pass_states:
            set_or_remove_state(hass, entity_id, state)
            assert cond(hass) is True
        for state in fail_states:
            set_or_remove_state(hass, entity_id, state)
            assert cond(hass) is False

    # Test invalid unit
    for limit_states in invalid_limit_entity_states:
        set_or_remove_state(hass, limit_entities[0], limit_states[0])
        set_or_remove_state(hass, limit_entities[1], limit_states[1])
        for state in pass_states:
            set_or_remove_state(hass, entity_id, state)
            assert cond(hass) is False
        for state in fail_states:
            set_or_remove_state(hass, entity_id, state)
            assert cond(hass) is False