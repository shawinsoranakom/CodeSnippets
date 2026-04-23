def test_is_manually_set(self):
        config._set_option("browser.serverAddress", "some.bucket", "test")
        self.assertEqual(True, config.is_manually_set("browser.serverAddress"))

        config._set_option("browser.serverAddress", "some.bucket", "<default>")
        self.assertEqual(False, config.is_manually_set("browser.serverAddress"))