async def test_schedule_install_setup_addon(
    addon_manager: AddonManager,
    install_addon: AsyncMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
) -> None:
    """Test schedule install setup addon."""
    install_task = addon_manager.async_schedule_install_setup_addon(
        {"test_key": "test"}
    )

    assert addon_manager.task_in_progress() is True

    # Make sure that actually only one install task is running.
    install_task_two = addon_manager.async_schedule_install_setup_addon(
        {"test_key": "test"}
    )

    await asyncio.gather(install_task, install_task_two)

    assert addon_manager.task_in_progress() is False
    assert install_addon.call_count == 1
    assert set_addon_options.call_count == 1
    assert start_addon.call_count == 1

    install_addon.reset_mock()
    set_addon_options.reset_mock()
    start_addon.reset_mock()

    # Test that another call can be made after the install is done.
    await addon_manager.async_schedule_install_setup_addon({"test_key": "test"})

    assert install_addon.call_count == 1
    assert set_addon_options.call_count == 1
    assert start_addon.call_count == 1