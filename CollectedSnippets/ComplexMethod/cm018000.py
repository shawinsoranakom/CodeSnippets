async def test_update_subentry_and_trigger_listener(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test that we can update subentry and trigger listener."""
    entry = MockConfigEntry(domain="test", options={"first": True})
    entry.add_to_manager(manager)
    update_listener_calls = []

    subentry = config_entries.ConfigSubentry(
        data={"test": "test"},
        subentry_type="test",
        unique_id="test",
        title="Mock title",
    )

    async def update_listener(
        hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> None:
        """Test function."""
        assert entry.subentries == expected_subentries
        update_listener_calls.append(None)

    entry.add_update_listener(update_listener)

    expected_subentries = {subentry.subentry_id: subentry}
    assert manager.async_add_subentry(entry, subentry) is True

    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.subentries == expected_subentries
    assert len(update_listener_calls) == 1

    assert (
        manager.async_update_subentry(
            entry,
            subentry,
            data={"test": "test2"},
            title="New title",
            unique_id="test2",
        )
        is True
    )

    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.subentries == expected_subentries
    assert len(update_listener_calls) == 2

    expected_subentries = {}
    assert manager.async_remove_subentry(entry, subentry.subentry_id) is True

    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.subentries == expected_subentries
    assert len(update_listener_calls) == 3