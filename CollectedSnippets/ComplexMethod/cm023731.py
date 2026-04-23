async def test_rename_entity_collision_without_states_meta_safeguard(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test states meta is not migrated when there is a collision.

    This test disables the safeguard in the states_meta_manager
    and relies on the filter_unique_constraint_integrity_error safeguard.
    """
    await async_setup_component(hass, "sensor", {})

    reg_entry = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique_0000",
        suggested_object_id="test1",
    )
    assert reg_entry.entity_id == "sensor.test1"
    await hass.async_block_till_done()

    zero, four, states = await async_record_states(hass)
    hist = history.get_significant_states(
        hass, zero, four, list(set(states) | {"sensor.test99", "sensor.test1"})
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)
    assert len(hist["sensor.test1"]) == 3

    hass.states.async_set("sensor.test99", "collision")
    hass.states.async_remove("sensor.test99")

    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    # Verify history before collision
    hist = history.get_significant_states(
        hass, zero, four, list(set(states) | {"sensor.test99", "sensor.test1"})
    )
    assert len(hist["sensor.test1"]) == 3
    assert len(hist["sensor.test99"]) == 2

    instance = recorder.get_instance(hass)
    # Patch out the safeguard in the states meta manager
    # so that we hit the filter_unique_constraint_integrity_error safeguard in the entity_registry
    with patch.object(instance.states_meta_manager, "get", return_value=None):
        # Rename entity sensor.test1 to sensor.test99
        entity_registry.async_update_entity(
            "sensor.test1", new_entity_id="sensor.test99"
        )
        await async_wait_recording_done(hass)

    # History is not migrated on collision
    hist = history.get_significant_states(
        hass, zero, four, list(set(states) | {"sensor.test99", "sensor.test1"})
    )
    assert len(hist["sensor.test1"]) == 3
    assert len(hist["sensor.test99"]) == 2

    with session_scope(hass=hass) as session:
        assert _count_entity_id_in_states_meta(hass, session, "sensor.test99") == 1

    hass.states.async_set("sensor.test99", "post_migrate")
    await async_wait_recording_done(hass)

    new_hist = history.get_significant_states(
        hass,
        zero,
        dt_util.utcnow(),
        list(set(states) | {"sensor.test99", "sensor.test1"}),
    )
    assert new_hist["sensor.test99"][-1].state == "post_migrate"
    assert len(hist["sensor.test99"]) == 2

    with session_scope(hass=hass) as session:
        assert _count_entity_id_in_states_meta(hass, session, "sensor.test99") == 1
        assert _count_entity_id_in_states_meta(hass, session, "sensor.test1") == 1

    # We should not hit the safeguard in the states_meta_manager
    assert "the new entity_id is already in use" not in caplog.text

    # We should hit the safeguard in the entity_registry
    assert "Blocked attempt to insert duplicated state rows" in caplog.text