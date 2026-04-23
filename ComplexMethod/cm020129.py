async def test_schedule_update_addon(
    addon_manager: AddonManager,
    addon_info: AsyncMock,
    create_backup: AsyncMock,
    update_addon: AsyncMock,
) -> None:
    """Test schedule update addon."""
    addon_info.return_value.update_available = True

    update_task = addon_manager.async_schedule_update_addon()

    assert addon_manager.task_in_progress() is True

    assert await addon_manager.async_get_addon_info() == AddonInfo(
        available=True,
        hostname="core-test-addon",
        options={},
        state=AddonState.UPDATING,
        update_available=True,
        version="1.0.0",
    )

    # Make sure that actually only one update task is running.
    update_task_two = addon_manager.async_schedule_update_addon()

    await asyncio.gather(update_task, update_task_two)

    assert addon_manager.task_in_progress() is False
    assert addon_info.call_count == 2
    assert create_backup.call_count == 1
    assert create_backup.call_args == call(
        PartialBackupOptions(name="addon_test_addon_1.0.0", addons={"test_addon"})
    )
    assert update_addon.call_count == 1

    update_addon.reset_mock()

    # Test that another call can be made after the update is done.
    await addon_manager.async_schedule_update_addon()

    assert update_addon.call_count == 1