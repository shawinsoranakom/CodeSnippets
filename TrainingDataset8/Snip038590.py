def test_check_conflicts_browser_serverport(self):
        config._set_option("global.developmentMode", True, "test")
        config._set_option("browser.serverPort", 1234, "test")
        with pytest.raises(AssertionError) as e:
            config._check_conflicts()
        self.assertEqual(
            str(e.value),
            "browser.serverPort does not work when global.developmentMode is true.",
        )