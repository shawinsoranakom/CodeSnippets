async def test_coordinator_entity(
    crd: update_coordinator.DataUpdateCoordinator[int],
) -> None:
    """Test the CoordinatorEntity class."""
    context = object()
    entity = update_coordinator.CoordinatorEntity(crd, context)

    assert entity.should_poll is False

    crd.last_update_success = False
    assert entity.available is False

    await entity.async_update()
    assert entity.available is True

    with patch(
        "homeassistant.helpers.entity.Entity.async_on_remove"
    ) as mock_async_on_remove:
        await entity.async_added_to_hass()

    mock_async_on_remove.assert_called_once()
    _on_remove_callback = mock_async_on_remove.call_args[0][0]

    # Verify we do not update if the entity is disabled
    crd.last_update_success = False
    with patch("homeassistant.helpers.entity.Entity.enabled", False):
        await entity.async_update()
    assert entity.available is False

    assert list(crd.async_contexts()) == [context]

    # Call remove callback to cleanup debouncer and avoid lingering timer
    assert len(crd._listeners) == 1
    _on_remove_callback()
    assert len(crd._listeners) == 0