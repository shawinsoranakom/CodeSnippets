def test_is_unset(self):
        config._set_option("browser.serverAddress", "some.bucket", "test")
        self.assertEqual(False, config._is_unset("browser.serverAddress"))

        config._set_option("browser.serverAddress", "some.bucket", "<default>")
        self.assertEqual(True, config._is_unset("browser.serverAddress"))