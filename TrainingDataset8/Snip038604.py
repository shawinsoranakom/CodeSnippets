def test_global_log_level_debug(self):
        config.set_option("global.developmentMode", True)
        self.assertEqual("debug", config.get_option("logger.level"))