async def test_raise_addon_task_in_progress(
    hass: HomeAssistant, install_addon: AsyncMock, start_addon: AsyncMock
) -> None:
    """Test raise ConfigEntryNotReady if an add-on task is in progress."""
    install_event = asyncio.Event()

    install_addon_original_side_effect = install_addon.side_effect

    async def install_addon_side_effect(slug: str) -> None:
        """Mock install add-on."""
        await install_event.wait()
        await install_addon_original_side_effect(slug)

    install_addon.side_effect = install_addon_side_effect

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Matter",
        data={
            "url": "ws://host1:5581/ws",
            "use_addon": True,
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await asyncio.sleep(0.05)

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 1
    assert start_addon.call_count == 0

    # Check that we only call install add-on once if a task is in progress.
    await hass.config_entries.async_reload(entry.entry_id)
    await asyncio.sleep(0.05)

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 1
    assert start_addon.call_count == 0

    install_event.set()
    await hass.async_block_till_done()

    assert install_addon.call_count == 1
    assert start_addon.call_count == 1