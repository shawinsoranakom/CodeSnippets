async def test_stop_shutdown_cancels_retry_setup_and_interval_listener(
    hass: HomeAssistant,
) -> None:
    """Test that shutdown will cancel scheduled a setup retry and interval listener."""
    async_setup_entry = Mock(side_effect=PlatformNotReady)
    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry()
    ent_platform = MockEntityPlatform(
        hass, platform_name=config_entry.domain, platform=platform
    )

    with patch.object(entity_platform, "async_call_later") as mock_call_later:
        assert not await ent_platform.async_setup_entry(config_entry)

    assert len(mock_call_later.mock_calls) == 1
    assert len(mock_call_later.return_value.mock_calls) == 0
    assert ent_platform._async_cancel_retry_setup is not None

    ent_platform.async_shutdown()

    assert len(mock_call_later.return_value.mock_calls) == 1
    assert ent_platform._async_polling_timer is None
    assert ent_platform._async_cancel_retry_setup is None