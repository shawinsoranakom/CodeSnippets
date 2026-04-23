async def test_async_enable_logging_supervisor(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    extra_env: dict[str, str],
    log_file_count: int,
    old_log_file_count: int,
) -> None:
    """Test to ensure the default log file is not created on Supervisor installations."""

    # Ensure we start with a clean slate
    cleanup_log_files()
    assert len(glob.glob(CONFIG_LOG_FILE)) == 0
    assert len(glob.glob(ARG_LOG_FILE)) == 0

    with (
        patch.dict(os.environ, {"SUPERVISOR": "1", **extra_env}),
        patch(
            "homeassistant.bootstrap.async_activate_log_queue_handler"
        ) as mock_async_activate_log_queue_handler,
        patch("logging.getLogger"),
    ):
        await bootstrap.async_enable_logging(hass)
        assert len(glob.glob(CONFIG_LOG_FILE)) == log_file_count
        mock_async_activate_log_queue_handler.assert_called_once()
        mock_async_activate_log_queue_handler.reset_mock()

        # Check that if the log file exists, it is renamed
        def write_log_file():
            with open(
                get_test_config_dir("home-assistant.log"), "w", encoding="utf8"
            ) as f:
                f.write("test")

        await hass.async_add_executor_job(write_log_file)
        assert len(glob.glob(CONFIG_LOG_FILE)) == 1
        assert len(glob.glob(f"{CONFIG_LOG_FILE}.old")) == 0

        await bootstrap.async_enable_logging(hass)
        assert len(glob.glob(CONFIG_LOG_FILE)) == log_file_count
        assert len(glob.glob(f"{CONFIG_LOG_FILE}.old")) == old_log_file_count
        mock_async_activate_log_queue_handler.assert_called_once()
        mock_async_activate_log_queue_handler.reset_mock()

        await bootstrap.async_enable_logging(
            hass,
            log_rotate_days=5,
            log_file="test.log",
        )
        mock_async_activate_log_queue_handler.assert_called_once()
        # Even on Supervisor, the log file should be created if it is explicitly specified
        assert len(glob.glob(ARG_LOG_FILE)) > 0

    cleanup_log_files()