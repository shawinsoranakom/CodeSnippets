def _session_state(draw) -> SessionState:
    state = SessionState()
    new_state = draw(NEW_SESSION_STATE)
    for k, v in new_state.items():
        state[k] = v

    unkeyed_widgets = draw(
        hst.dictionaries(keys=UNKEYED_WIDGET_IDS, values=hst.integers())
    )
    for wid, v in unkeyed_widgets.items():
        state.register_widget(mock_metadata(wid, v), user_key=None)

    widget_key_val_triple = draw(
        hst.lists(hst.tuples(hst.uuids(), USER_KEY, hst.integers()))
    )
    k_wids = {
        key: (as_keyed_widget_id(wid, key), val)
        for wid, key, val in widget_key_val_triple
    }
    for key, (wid, val) in k_wids.items():
        state.register_widget(mock_metadata(wid, val), user_key=key)

    if k_wids:
        session_state_widget_entries = draw(
            hst.dictionaries(
                keys=hst.sampled_from(list(k_wids.keys())),
                values=hst.integers(),
            )
        )
        for k, v in session_state_widget_entries.items():
            state[k] = v

    return state