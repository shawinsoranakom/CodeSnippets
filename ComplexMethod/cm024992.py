async def test_async_set_updated_data(
    crd: update_coordinator.DataUpdateCoordinator[int],
) -> None:
    """Test async_set_updated_data for update coordinator."""
    assert crd.data is None

    with patch.object(crd._debounced_refresh, "async_cancel") as mock_cancel:
        crd.async_set_updated_data(100)

        # Test we cancel any pending refresh
        assert len(mock_cancel.mock_calls) == 1

    # Test data got updated
    assert crd.data == 100
    assert crd.last_update_success is True

    # Make sure we didn't schedule a refresh because we have 0 listeners
    assert crd._unsub_refresh is None

    updates = []

    def update_callback():
        updates.append(crd.data)

    remove_callbacks = crd.async_add_listener(update_callback)
    crd.async_set_updated_data(200)
    assert updates == [200]
    assert crd._unsub_refresh is not None

    old_refresh = crd._unsub_refresh

    crd.async_set_updated_data(300)
    # We have created a new refresh listener
    assert crd._unsub_refresh is not old_refresh

    # Remove callbacks to avoid lingering timers
    remove_callbacks()