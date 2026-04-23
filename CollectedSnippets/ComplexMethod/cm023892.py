async def test_stale_entities_removed_on_config_change(
    hass: HomeAssistant,
    mock_two_button_config_entry: MockConfigEntry,
    mock_opendisplay_device: MagicMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Entities for buttons no longer in device config are removed on reload."""
    mock_two_button_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_two_button_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        len(
            [
                e
                for e in er.async_entries_for_config_entry(
                    entity_registry, mock_two_button_config_entry.entry_id
                )
                if e.domain == "event"
            ]
        )
        == 2
    )

    # Device reconfigured: now only 1 active button
    mock_opendisplay_device.config = make_button_device_config(
        [make_binary_inputs(input_flags=0x01)]
    )
    assert await hass.config_entries.async_unload(mock_two_button_config_entry.entry_id)
    assert await hass.config_entries.async_setup(mock_two_button_config_entry.entry_id)
    await hass.async_block_till_done()

    event_entries = [
        e
        for e in er.async_entries_for_config_entry(
            entity_registry, mock_two_button_config_entry.entry_id
        )
        if e.domain == "event"
    ]
    assert len(event_entries) == 1
    assert event_entries[0].unique_id == f"{TEST_ADDRESS}-button_0_0"