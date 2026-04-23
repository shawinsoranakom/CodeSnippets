async def test_shutdown(
    hass: HomeAssistant, crd: update_coordinator.DataUpdateCoordinator[int]
) -> None:
    """Test async_shutdown for update coordinator."""
    assert crd.data is None
    await crd.async_refresh()
    assert crd.data == 1
    assert crd.last_update_success is True
    # Make sure we didn't schedule a refresh because we have 0 listeners
    assert crd._unsub_refresh is None

    updates = []

    def update_callback():
        updates.append(crd.data)

    _ = crd.async_add_listener(update_callback)
    await crd.async_refresh()
    assert updates == [2]
    assert crd._unsub_refresh is not None

    # Test shutdown through function
    with patch.object(crd._debounced_refresh, "async_shutdown") as mock_shutdown:
        await crd.async_shutdown()

    async_fire_time_changed(hass, utcnow() + crd.update_interval)
    await hass.async_block_till_done()

    # Test we shutdown the debouncer and cleared the subscriptions
    assert len(mock_shutdown.mock_calls) == 1
    assert crd._unsub_refresh is None

    await crd.async_refresh()
    assert updates == [2]