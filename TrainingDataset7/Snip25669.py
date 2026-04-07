def setUpClass(cls):
        super().setUpClass()
        logging.config.dictConfig(DEFAULT_LOGGING)
        cls.addClassCleanup(logging.config.dictConfig, settings.LOGGING)