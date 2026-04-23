def test_descendent_loggers_depend_on_and_propagate_logs_to_root_logger(monkeypatch):
    """This test presumes that VLLM_CONFIGURE_LOGGING (default: True) and
    VLLM_LOGGING_CONFIG_PATH (default: None) are not configured and default
    behavior is activated."""
    monkeypatch.setenv("VLLM_CONFIGURE_LOGGING", "1")
    monkeypatch.delenv("VLLM_LOGGING_CONFIG_PATH", raising=False)

    root_logger = logging.getLogger("vllm")
    root_handler = root_logger.handlers[0]

    unique_name = f"vllm.{uuid4()}"
    logger = init_logger(unique_name)
    assert logger.name == unique_name
    assert logger.level == logging.NOTSET
    assert not logger.handlers
    assert logger.propagate

    message = "Hello, world!"
    with patch.object(root_handler, "emit") as root_handle_mock:
        logger.info(message)

    root_handle_mock.assert_called_once()
    _, call_args, _ = root_handle_mock.mock_calls[0]
    log_record = call_args[0]
    assert unique_name == log_record.name
    assert message == log_record.msg
    assert message == log_record.msg
    assert log_record.levelno == logging.INFO