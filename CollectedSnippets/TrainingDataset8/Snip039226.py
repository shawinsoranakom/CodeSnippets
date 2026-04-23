def test_init_tornado_logs(self):
        """Test streamlit.logger.init_tornado_logs."""
        logger.init_tornado_logs()
        loggers = [x for x in logger._loggers.keys() if "tornado." in x]
        truth = ["tornado.access", "tornado.application", "tornado.general"]
        self.assertEqual(sorted(truth), sorted(loggers))