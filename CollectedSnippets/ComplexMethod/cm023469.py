async def test_add_and_remove_work_area(
    hass: HomeAssistant,
    mock_automower_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    entity_registry: er.EntityRegistry,
    values: dict[str, MowerAttributes],
) -> None:
    """Test adding a work area in runtime."""
    websocket_values = deepcopy(values)
    callback_holder: dict[str, Callable] = {}

    @callback
    def fake_register_websocket_response(
        cb: Callable[[dict[str, MowerAttributes]], None],
    ) -> None:
        callback_holder["cb"] = cb

    mock_automower_client.register_data_callback.side_effect = (
        fake_register_websocket_response
    )
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    current_entites_start = len(
        er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    )
    await hass.async_block_till_done()

    assert mock_automower_client.register_data_callback.called
    assert "cb" in callback_holder

    new_task = Calendar(
        start=dt_time(hour=11),
        duration=timedelta(60),
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=True,
        friday=True,
        saturday=True,
        sunday=True,
        work_area_id=1,
    )
    websocket_values[TEST_MOWER_ID].calendar.tasks.append(new_task)
    poll_values = deepcopy(websocket_values)
    poll_values[TEST_MOWER_ID].work_area_names.append("new work area")
    poll_values[TEST_MOWER_ID].work_area_dict.update({1: "new work area"})
    poll_values[TEST_MOWER_ID].work_areas.update(
        {
            1: WorkArea(
                name="new work area",
                cutting_height=12,
                enabled=True,
                progress=12,
                last_time_completed=datetime(
                    2024, 10, 1, 11, 11, 0, tzinfo=dt_util.get_default_time_zone()
                ),
            )
        }
    )
    mock_automower_client.get_status.return_value = poll_values

    callback_holder["cb"](websocket_values)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.called

    state = hass.states.get("sensor.test_mower_1_new_work_area_progress")
    assert state is not None
    assert state.state == "12"
    current_entites_after_addition = len(
        er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    )
    assert (
        current_entites_after_addition
        == current_entites_start
        + ADDITIONAL_NUMBER_ENTITIES
        + ADDITIONAL_SENSOR_ENTITIES
        + ADDITIONAL_SWITCH_ENTITIES
    )

    poll_values[TEST_MOWER_ID].work_area_names.remove("new work area")
    del poll_values[TEST_MOWER_ID].work_area_dict[1]
    del poll_values[TEST_MOWER_ID].work_areas[1]
    poll_values[TEST_MOWER_ID].work_area_names.remove("Front lawn")
    del poll_values[TEST_MOWER_ID].work_area_dict[123456]
    del poll_values[TEST_MOWER_ID].work_areas[123456]

    poll_values[TEST_MOWER_ID].calendar.tasks = [
        task
        for task in poll_values[TEST_MOWER_ID].calendar.tasks
        if task.work_area_id not in [1, 123456]
    ]

    poll_values[TEST_MOWER_ID].mower.work_area_id = 654321
    mock_automower_client.get_status.return_value = poll_values
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    current_entites_after_deletion = len(
        er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    )
    assert (
        current_entites_after_deletion
        == current_entites_start
        - ADDITIONAL_SWITCH_ENTITIES
        - ADDITIONAL_NUMBER_ENTITIES
        - ADDITIONAL_SENSOR_ENTITIES
    )