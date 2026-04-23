def make_handler(self, **formatter_kwargs):
        formatter = QueryFormatter(**formatter_kwargs)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)

        original_level = logger.getEffectiveLevel()
        logger.setLevel(logging.DEBUG)
        self.addCleanup(logger.setLevel, original_level)
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)

        return handler