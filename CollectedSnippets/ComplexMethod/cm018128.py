def parametrize_trigger_states(
    *,
    trigger: str,
    trigger_options: dict[str, Any] | None = None,
    target_states: list[str | None | tuple[str | None, dict]],
    other_states: list[str | None | tuple[str | None, dict]],
    extra_invalid_states: list[str | None | tuple[str | None, dict]] | None = None,
    required_filter_attributes: dict | None = None,
    trigger_from_none: bool = True,
    retrigger_on_target_state: bool = False,
) -> list[tuple[str, dict[str, Any], list[TriggerStateDescription]]]:
    """Parametrize states and expected service call counts.

    The target_states, other_states, and extra_invalid_states iterables are
    either iterables of states or iterables of (state, attributes) tuples.

    Set `trigger_from_none` to False if the trigger is not expected to fire
    when the initial state is None, this is relevant for triggers that limit
    entities to a certain device class because the device class can't be
    determined when the state is None.

    Set `retrigger_on_target_state` to True if the trigger is expected to fire
    when the state changes to another target state.

    Returns a list of tuples with (trigger, list of states),
    where states is a list of TriggerStateDescription dicts.
    """

    extra_invalid_states = extra_invalid_states or []
    invalid_states = [STATE_UNAVAILABLE, STATE_UNKNOWN, *extra_invalid_states]
    required_filter_attributes = required_filter_attributes or {}
    trigger_options = trigger_options or {}

    def state_with_attributes(
        state: str | None | tuple[str | None, dict], count: int
    ) -> TriggerStateDescription:
        """Return TriggerStateDescription dict."""
        if isinstance(state, str) or state is None:
            return {
                "included_state": {
                    "state": state,
                    "attributes": required_filter_attributes,
                },
                "excluded_state": {
                    "state": state if required_filter_attributes else None,
                    "attributes": {},
                },
                "count": count,
            }
        return {
            "included_state": {
                "state": state[0],
                "attributes": state[1] | required_filter_attributes,
            },
            "excluded_state": {
                "state": state[0] if required_filter_attributes else None,
                "attributes": state[1],
            },
            "count": count,
        }

    tests = [
        # Initial state None
        (
            trigger,
            trigger_options,
            list(
                itertools.chain.from_iterable(
                    (
                        state_with_attributes(None, 0),
                        state_with_attributes(target_state, 0),
                        state_with_attributes(other_state, 0),
                        state_with_attributes(
                            target_state, 1 if trigger_from_none else 0
                        ),
                    )
                    for target_state in target_states
                    for other_state in other_states
                )
            ),
        ),
        # Initial state different from target state
        (
            trigger,
            trigger_options,
            list(
                itertools.chain.from_iterable(
                    (
                        state_with_attributes(other_state, 0),
                        state_with_attributes(target_state, 1),
                        state_with_attributes(other_state, 0),
                        state_with_attributes(target_state, 1),
                    )
                    for target_state in target_states
                    for other_state in other_states
                )
            ),
        ),
        # Initial state same as target state
        (
            trigger,
            trigger_options,
            list(
                itertools.chain.from_iterable(
                    (
                        state_with_attributes(target_state, 0),
                        state_with_attributes(target_state, 0),
                        state_with_attributes(other_state, 0),
                        state_with_attributes(target_state, 1),
                        # Repeat target state to test retriggering
                        state_with_attributes(target_state, 0),
                        state_with_attributes(STATE_UNAVAILABLE, 0),
                    )
                    for target_state in target_states
                    for other_state in other_states
                )
            ),
        ),
        # Transition from other state to unavailable / unknown
        (
            trigger,
            trigger_options,
            list(
                itertools.chain.from_iterable(
                    (
                        state_with_attributes(other_state, 0),
                        state_with_attributes(invalid_state, 0),
                        state_with_attributes(other_state, 0),
                        state_with_attributes(target_state, 1),
                    )
                    for invalid_state in invalid_states
                    for target_state in target_states
                    for other_state in other_states
                )
            ),
        ),
        # Initial state unavailable / unknown + extra invalid states
        (
            trigger,
            trigger_options,
            list(
                itertools.chain.from_iterable(
                    (
                        state_with_attributes(invalid_state, 0),
                        state_with_attributes(target_state, 0),
                        state_with_attributes(other_state, 0),
                        state_with_attributes(target_state, 1),
                    )
                    for invalid_state in invalid_states
                    for target_state in target_states
                    for other_state in other_states
                )
            ),
        ),
    ]

    if len(target_states) > 1:
        # If more than one target state, test state change between target states
        tests.append(
            (
                trigger,
                trigger_options,
                list(
                    itertools.chain.from_iterable(
                        (
                            state_with_attributes(target_states[idx - 1], 0),
                            state_with_attributes(
                                target_state, 1 if retrigger_on_target_state else 0
                            ),
                            state_with_attributes(other_state, 0),
                            state_with_attributes(target_states[idx - 1], 1),
                            state_with_attributes(
                                target_state, 1 if retrigger_on_target_state else 0
                            ),
                            state_with_attributes(STATE_UNAVAILABLE, 0),
                        )
                        for idx, target_state in enumerate(target_states[1:], start=1)
                        for other_state in other_states
                    )
                ),
            ),
        )

    return tests