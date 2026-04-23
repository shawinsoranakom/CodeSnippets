async def test_select_entity_changing_pipelines(
    hass: HomeAssistant,
    init_select: MockConfigEntry,
    pipeline_1: Pipeline,
    pipeline_2: Pipeline,
    pipeline_storage: PipelineStorageCollection,
) -> None:
    """Test entity tracking pipeline changes."""
    config_entry = init_select  # nicer naming
    config_entry.mock_state(hass, ConfigEntryState.LOADED)

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == "preferred"
    assert state.attributes["options"] == [
        "preferred",
        "Home Assistant",
        pipeline_1.name,
        pipeline_2.name,
    ]

    # Change select to new pipeline
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.assist_pipeline_test_prefix_pipeline",
            "option": pipeline_2.name,
        },
        blocking=True,
    )

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == pipeline_2.name

    # Reload config entry to test selected option persists
    assert await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.SELECT
    )
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.SELECT]
    )

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == pipeline_2.name

    # Remove selected pipeline
    await pipeline_storage.async_delete_item(pipeline_2.id)

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == "preferred"
    assert state.attributes["options"] == [
        "preferred",
        "Home Assistant",
        pipeline_1.name,
    ]