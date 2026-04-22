def test_global_log_level(self):
        config.set_option("global.developmentMode", False)
        self.assertEqual("info", config.get_option("logger.level"))