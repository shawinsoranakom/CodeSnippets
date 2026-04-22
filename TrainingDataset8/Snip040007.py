def session_state(draw) -> SessionState:
    state = draw(_session_state())

    state._compact_state()
    # round 2

    state2 = draw(_session_state())

    _merge_states(state, state2)

    return state