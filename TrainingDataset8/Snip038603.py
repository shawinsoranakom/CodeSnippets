def test_global_dev_mode(self):
        config.set_option("global.developmentMode", True)
        self.assertEqual(True, config.get_option("global.developmentMode"))