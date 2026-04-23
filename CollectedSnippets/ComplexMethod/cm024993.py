async def test_async_set_update_error(
    crd: update_coordinator.DataUpdateCoordinator[int], caplog: pytest.LogCaptureFixture
) -> None:
    """Test manually setting an update failure."""
    update_callback = Mock()
    remove_callbacks = crd.async_add_listener(update_callback)

    crd.async_set_update_error(aiohttp.ClientError("Client Failure #1"))
    assert crd.last_update_success is False
    assert "Client Failure #1" in caplog.text
    update_callback.assert_called_once()
    update_callback.reset_mock()

    # Additional failure does not log or change state
    crd.async_set_update_error(aiohttp.ClientError("Client Failure #2"))
    assert crd.last_update_success is False
    assert "Client Failure #2" not in caplog.text
    update_callback.assert_not_called()
    update_callback.reset_mock()

    crd.async_set_updated_data(200)
    assert crd.last_update_success is True
    update_callback.assert_called_once()
    update_callback.reset_mock()

    crd.async_set_update_error(aiohttp.ClientError("Client Failure #3"))
    assert crd.last_update_success is False
    assert "Client Failure #2" not in caplog.text
    update_callback.assert_called_once()

    # Remove callbacks to avoid lingering timers
    remove_callbacks()