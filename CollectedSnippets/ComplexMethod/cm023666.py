async def test_saving_state_with_oversized_attributes(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    setup_recorder: None,
) -> None:
    """Test saving states is limited to 16KiB of JSON encoded attributes."""
    massive_dict = {"a": "b" * 16384}
    attributes = {"test_attr": 5, "test_attr_10": "nice"}
    hass.states.async_set("switch.sane", "on", attributes)
    hass.states.async_set("switch.too_big", "on", massive_dict)
    await async_wait_recording_done(hass)
    states = []

    with session_scope(hass=hass, read_only=True) as session:
        for db_state, db_state_attributes, states_meta in (
            session.query(States, StateAttributes, StatesMeta)
            .outerjoin(
                StateAttributes, States.attributes_id == StateAttributes.attributes_id
            )
            .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
        ):
            db_state.entity_id = states_meta.entity_id
            native_state = db_state_to_native(db_state)
            native_state.attributes = db_state_attributes_to_native(db_state_attributes)
            states.append(native_state)

    assert "switch.too_big" in caplog.text

    assert len(states) == 2
    assert _state_with_context(hass, "switch.sane").as_dict() == states[0].as_dict()
    assert states[1].state == "on"
    assert states[1].entity_id == "switch.too_big"
    assert states[1].attributes == {}