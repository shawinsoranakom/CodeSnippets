def test_handlers_added_correctly():
    """Test if the handlers are added correctly."""
    with (
        patch(
            "openbb_core.app.logs.handlers_manager.PathTrackingFileHandler",
            MockPathTrackingFileHandler,
        ),
        patch(
            "openbb_core.app.logs.handlers_manager.FormatterWithExceptions",
            MockFormatterWithExceptions,
        ),
    ):
        settings = Mock()
        settings.verbosity = 20
        settings.handler_list = ["stdout", "stderr", "noop", "file"]
        settings.logging_suppress = False
        logger = logging.getLogger("test_handlers_added_correctly")
        handlers_manager = HandlersManager(logger=logger, settings=settings)
        handlers_manager.setup()
        handlers = logger.handlers

        assert not logger.propagate
        assert logger.level == 20
        assert len(handlers) >= 4

        for handler in handlers:
            assert isinstance(
                handler,
                (
                    logging.NullHandler,
                    logging.StreamHandler,
                    PathTrackingFileHandler,
                ),
            )

        for mock in [MockPathTrackingFileHandler]:
            assert any(isinstance(handler, mock) for handler in handlers)