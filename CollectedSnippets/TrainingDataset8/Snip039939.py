def _compact_copy(state: SessionState) -> SessionState:
    """Return a compacted copy of the given SessionState."""
    state_copy = deepcopy(state)
    state_copy._compact_state()
    return state_copy