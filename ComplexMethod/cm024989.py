async def test_async_refresh(
    crd: update_coordinator.DataUpdateCoordinator[int],
) -> None:
    """Test async_refresh for update coordinator."""
    assert crd.data is None
    await crd.async_refresh()
    assert crd.data == 1
    assert crd.last_update_success is True
    # Make sure we didn't schedule a refresh because we have 0 listeners
    assert crd._unsub_refresh is None

    updates = []

    def update_callback():
        updates.append(crd.data)

    unsub = crd.async_add_listener(update_callback)
    await crd.async_refresh()
    assert updates == [2]
    assert crd._unsub_refresh is not None

    # Test unsubscribing through function
    unsub()
    await crd.async_refresh()
    assert updates == [2]