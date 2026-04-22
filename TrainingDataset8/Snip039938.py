def check_roundtrip(widget_id: str, value: Any) -> None:
    session_state = _raw_session_state()
    wid = session_state._get_widget_id(widget_id)
    metadata = session_state._new_widget_state.widget_metadata[wid]
    serializer = metadata.serializer
    deserializer = metadata.deserializer

    assert deserializer(serializer(value), "") == value