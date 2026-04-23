async def test_multiple_binary_input_instances(
    hass: HomeAssistant,
    mock_multi_instance_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Entities across multiple BinaryInputs instances get globally sequential button numbers."""
    mock_multi_instance_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(
        mock_multi_instance_config_entry.entry_id
    )
    await hass.async_block_till_done()

    entries = er.async_entries_for_config_entry(
        entity_registry, mock_multi_instance_config_entry.entry_id
    )
    event_entries = [e for e in entries if e.domain == "event"]
    assert len(event_entries) == 3
    assert {e.unique_id for e in event_entries} == {
        f"{TEST_ADDRESS}-button_0_0",
        f"{TEST_ADDRESS}-button_0_1",
        f"{TEST_ADDRESS}-button_1_0",
    }
    # Button numbers must be globally sequential, not reset per instance
    names = {
        e.unique_id: hass.states.get(e.entity_id).attributes.get("friendly_name", "")
        for e in event_entries
    }
    assert names[f"{TEST_ADDRESS}-button_0_0"].endswith("Button 1")
    assert names[f"{TEST_ADDRESS}-button_0_1"].endswith("Button 2")
    assert names[f"{TEST_ADDRESS}-button_1_0"].endswith("Button 3")