def _merge_states(a: SessionState, b: SessionState) -> None:
    """Merge 'b' into 'a'."""
    a._new_session_state.update(b._new_session_state)
    a._new_widget_state.update(b._new_widget_state)
    a._old_state.update(b._old_state)
    a._key_id_mapping.update(b._key_id_mapping)