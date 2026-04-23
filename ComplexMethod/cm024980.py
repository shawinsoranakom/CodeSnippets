async def test_platform_slow_setup_cancel_warning(hass: HomeAssistant) -> None:
    """Test slow setup warning timer is scheduled and cancelled on success."""
    platform = MockPlatform()

    mock_platform(hass, "platform.test_domain", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    call_at_handles: list[tuple[tuple, MagicMock]] = []

    def mock_call_at(*args: Any, **kwargs: Any) -> MagicMock:
        handle = MagicMock()
        call_at_handles.append((args, handle))
        return handle

    with patch.object(hass.loop, "call_at", side_effect=mock_call_at):
        await component.async_setup({DOMAIN: {"platform": "platform"}})
        await hass.async_block_till_done()
        assert call_at_handles

        # Find the platform setup warning by matching the exact format string
        warn_args, warn_handle = next(
            (args, handle)
            for args, handle in call_at_handles
            if len(args) >= 3
            and args[1] == _LOGGER.warning
            and args[2] == "Setup of %s platform %s is taking over %s seconds."
        )

        assert warn_args[0] - hass.loop.time() == pytest.approx(
            entity_platform.SLOW_SETUP_WARNING, 0.5
        )
        assert warn_handle.cancel.call_count == 1