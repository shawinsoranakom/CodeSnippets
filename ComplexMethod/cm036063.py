def test_default_vllm_root_logger_configuration(monkeypatch):
    """This test presumes that VLLM_CONFIGURE_LOGGING (default: True) and
    VLLM_LOGGING_CONFIG_PATH (default: None) are not configured and default
    behavior is activated."""
    monkeypatch.setenv("VLLM_LOGGING_COLOR", "0")
    _configure_vllm_root_logger()

    logger = logging.getLogger("vllm")
    assert logger.level == logging.INFO
    assert not logger.propagate

    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream == sys.stdout
    # we use DEBUG level for testing by default
    # assert handler.level == logging.INFO

    formatter = handler.formatter
    assert formatter is not None
    assert isinstance(formatter, NewLineFormatter)
    assert formatter._fmt == _FORMAT
    assert formatter.datefmt == _DATE_FORMAT