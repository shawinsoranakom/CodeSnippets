async def test_rename_entity_on_mocked_platform(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test states meta is migrated when entity_id is changed when using a mocked platform.

    This test will call async_remove on the entity so we can make
    sure that we do not record the entity as removed in the database
    when we rename it.
    """
    instance = recorder.get_instance(hass)
    start = dt_util.utcnow()

    reg_entry = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique_0000",
        suggested_object_id="test1",
    )
    assert reg_entry.entity_id == "sensor.test1"

    entity_platform1 = MockEntityPlatform(
        hass, domain="mock_integration", platform_name="mock_platform", platform=None
    )
    entity1 = MockEntity(entity_id=reg_entry.entity_id)
    await entity_platform1.async_add_entities([entity1])

    await hass.async_block_till_done()

    hass.states.async_set("sensor.test1", "pre_migrate")
    await async_wait_recording_done(hass)

    hist = await instance.async_add_executor_job(
        history.get_significant_states,
        hass,
        start,
        None,
        ["sensor.test1", "sensor.test99"],
    )

    entity_registry.async_update_entity("sensor.test1", new_entity_id="sensor.test99")
    await hass.async_block_till_done()
    # We have to call the remove method ourselves since we are mocking the platform
    hass.states.async_remove("sensor.test1")

    # The remove will trigger a lookup of the non-existing entity_id in the database
    # so we need to force the recorder to return the connection to the pool
    # since our test setup only allows one connection at a time.
    instance.queue_task(ForceReturnConnectionToPool())

    await async_wait_recording_done(hass)

    hist = await instance.async_add_executor_job(
        history.get_significant_states,
        hass,
        start,
        None,
        ["sensor.test1", "sensor.test99"],
    )

    assert "sensor.test1" not in hist
    # Make sure the states manager has not leaked the old entity_id
    assert instance.states_manager.pop_committed("sensor.test1") is None
    assert instance.states_manager.pop_pending("sensor.test1") is None

    hass.states.async_set("sensor.test99", "post_migrate")
    await async_wait_recording_done(hass)

    new_hist = await instance.async_add_executor_job(
        history.get_significant_states,
        hass,
        start,
        None,
        ["sensor.test1", "sensor.test99"],
    )

    assert "sensor.test1" not in new_hist
    assert new_hist["sensor.test99"][-1].state == "post_migrate"

    def _get_states_meta_counts():
        with session_scope(hass=hass) as session:
            return _count_entity_id_in_states_meta(
                hass, session, "sensor.test99"
            ), _count_entity_id_in_states_meta(hass, session, "sensor.test1")

    test99_count, test1_count = await instance.async_add_executor_job(
        _get_states_meta_counts
    )
    assert test99_count == 1
    assert test1_count == 1

    assert "the new entity_id is already in use" not in caplog.text