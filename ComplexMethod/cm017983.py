async def test_setup_hass(
    mock_enable_logging: AsyncMock,
    mock_is_virtual_env: Mock,
    mock_mount_local_lib_path: AsyncMock,
    mock_ensure_config_exists: AsyncMock,
    mock_process_ha_config_upgrade: Mock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test it works."""
    verbose = Mock()
    log_rotate_days = Mock()
    log_file = Mock()
    log_no_color = Mock()

    with patch.object(bootstrap, "LOG_SLOW_STARTUP_INTERVAL", 5000):
        hass = await bootstrap.async_setup_hass(
            runner.RuntimeConfig(
                config_dir=get_test_config_dir(),
                verbose=verbose,
                log_rotate_days=log_rotate_days,
                log_file=log_file,
                log_no_color=log_no_color,
                skip_pip=True,
                recovery_mode=False,
                debug=True,
            ),
        )

    assert "Waiting for integrations to complete setup" not in caplog.text

    assert "browser" in hass.config.components
    assert "recovery_mode" not in hass.config.components

    assert len(mock_enable_logging.mock_calls) == 1
    assert mock_enable_logging.mock_calls[0][1] == (
        hass,
        verbose,
        log_rotate_days,
        log_file,
        log_no_color,
    )
    assert len(mock_mount_local_lib_path.mock_calls) == 1
    assert len(mock_ensure_config_exists.mock_calls) == 1
    assert len(mock_process_ha_config_upgrade.mock_calls) == 1

    # debug in RuntimeConfig should set it it in hass.config
    assert hass.config.debug is True

    assert hass == async_get_hass()